use log::{error, info, warn};
use std::sync::Arc;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::RwLock;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use crate::meter::Meter;

pub struct ModbusServer {
    meter: Arc<RwLock<Meter>>,
}

impl ModbusServer {
    pub fn new(meter: Arc<RwLock<Meter>>) -> Self {
        Self { meter }
    }
    
    pub async fn start(&self, address: &str, port: u16) -> Result<(), Box<dyn std::error::Error>> {
        let socket_addr = format!("{}:{}", address, port);
        let listener = TcpListener::bind(&socket_addr).await?;
        
        info!("Modbus TCP server started on {}", socket_addr);
        
        loop {
            match listener.accept().await {
                Ok((stream, addr)) => {
                    info!("New client connection from: {}", addr);
                    let meter = self.meter.clone();
                    tokio::spawn(async move {
                        if let Err(e) = handle_connection(stream, meter).await {
                            error!("Error handling connection from {}: {}", addr, e);
                        }
                    });
                }
                Err(e) => {
                    error!("Failed to accept connection: {}", e);
                }
            }
        }
    }
}

async fn handle_connection(
    mut stream: TcpStream, 
    meter: Arc<RwLock<Meter>>
) -> Result<(), Box<dyn std::error::Error>> {
    let mut buffer = [0u8; 260]; // Modbus TCP max frame size
    
    loop {
        match stream.read(&mut buffer).await {
            Ok(0) => {
                info!("Client disconnected");
                break;
            }
            Ok(bytes_read) => {
                if bytes_read < 8 {
                    warn!("Received incomplete Modbus frame");
                    continue;
                }
                
                let response = process_modbus_request(&buffer[..bytes_read], &meter).await;
                if let Some(response_data) = response {
                    if let Err(e) = stream.write_all(&response_data).await {
                        error!("Failed to write response: {}", e);
                        break;
                    }
                }
            }
            Err(e) => {
                error!("Failed to read from stream: {}", e);
                break;
            }
        }
    }
    
    Ok(())
}

async fn process_modbus_request(
    request: &[u8], 
    meter: &Arc<RwLock<Meter>>
) -> Option<Vec<u8>> {
    if request.len() < 8 {
        return None;
    }
    
    // Parse Modbus TCP header
    let transaction_id = u16::from_be_bytes([request[0], request[1]]);
    let protocol_id = u16::from_be_bytes([request[2], request[3]]);
    let length = u16::from_be_bytes([request[4], request[5]]);
    let unit_id = request[6];
    let function_code = request[7];
    
    if protocol_id != 0 {
        warn!("Invalid protocol ID: {}", protocol_id);
        return None;
    }
    
    match function_code {
        0x03 => handle_read_holding_registers(request, meter, transaction_id, unit_id).await,
        0x04 => handle_read_input_registers(request, meter, transaction_id, unit_id).await,
        0x01 => handle_read_coils(request, meter, transaction_id, unit_id).await,
        0x02 => handle_read_discrete_inputs(request, meter, transaction_id, unit_id).await,
        0x05 => handle_write_single_coil(request, meter, transaction_id, unit_id).await,
        0x06 => handle_write_single_register(request, meter, transaction_id, unit_id).await,
        _ => {
            warn!("Unsupported function code: {}", function_code);
            create_exception_response(transaction_id, unit_id, function_code, 0x01) // Illegal function
        }
    }
}

async fn handle_read_holding_registers(
    request: &[u8],
    meter: &Arc<RwLock<Meter>>,
    transaction_id: u16,
    unit_id: u8,
) -> Option<Vec<u8>> {
    if request.len() < 12 {
        return create_exception_response(transaction_id, unit_id, 0x03, 0x03);
    }
    
    let start_address = u16::from_be_bytes([request[8], request[9]]);
    let quantity = u16::from_be_bytes([request[10], request[11]]);
    
    if quantity == 0 || quantity > 125 {
        return create_exception_response(transaction_id, unit_id, 0x03, 0x03);
    }
    
    let meter_lock = meter.read().await;
    let mut response_data = Vec::new();
    
    for i in 0..quantity {
        let address = start_address + i;
        let value = meter_lock.get_register_value(address);
        response_data.push((value >> 8) as u8);  // High byte
        response_data.push((value & 0xFF) as u8); // Low byte
    }
    
    let byte_count = (quantity * 2) as u8;
    let length = 3 + byte_count as u16;
    
    let mut response = Vec::new();
    response.extend_from_slice(&transaction_id.to_be_bytes());
    response.extend_from_slice(&0u16.to_be_bytes()); // Protocol ID
    response.extend_from_slice(&length.to_be_bytes());
    response.push(unit_id);
    response.push(0x03); // Function code
    response.push(byte_count);
    response.extend_from_slice(&response_data);
    
    Some(response)
}

async fn handle_read_input_registers(
    request: &[u8],
    meter: &Arc<RwLock<Meter>>,
    transaction_id: u16,
    unit_id: u8,
) -> Option<Vec<u8>> {
    // For this simulator, input registers are the same as holding registers
    handle_read_holding_registers(request, meter, transaction_id, unit_id).await
}

async fn handle_read_coils(
    request: &[u8],
    meter: &Arc<RwLock<Meter>>,
    transaction_id: u16,
    unit_id: u8,
) -> Option<Vec<u8>> {
    if request.len() < 12 {
        return create_exception_response(transaction_id, unit_id, 0x01, 0x03);
    }
    
    let start_address = u16::from_be_bytes([request[8], request[9]]);
    let quantity = u16::from_be_bytes([request[10], request[11]]);
    
    if quantity == 0 || quantity > 2000 {
        return create_exception_response(transaction_id, unit_id, 0x01, 0x03);
    }
    
    let meter_lock = meter.read().await;
    let byte_count = ((quantity + 7) / 8) as u8;
    let mut response_data = vec![0u8; byte_count as usize];
    
    for i in 0..quantity {
        let address = start_address + i;
        if meter_lock.get_coil_value(address) {
            let byte_index = (i / 8) as usize;
            let bit_index = i % 8;
            response_data[byte_index] |= 1 << bit_index;
        }
    }
    
    let length = 3 + byte_count as u16;
    
    let mut response = Vec::new();
    response.extend_from_slice(&transaction_id.to_be_bytes());
    response.extend_from_slice(&0u16.to_be_bytes()); // Protocol ID
    response.extend_from_slice(&length.to_be_bytes());
    response.push(unit_id);
    response.push(0x01); // Function code
    response.push(byte_count);
    response.extend_from_slice(&response_data);
    
    Some(response)
}

async fn handle_read_discrete_inputs(
    request: &[u8],
    meter: &Arc<RwLock<Meter>>,
    transaction_id: u16,
    unit_id: u8,
) -> Option<Vec<u8>> {
    // For this simulator, discrete inputs are the same as coils
    handle_read_coils(request, meter, transaction_id, unit_id).await
}

async fn handle_write_single_coil(
    request: &[u8],
    meter: &Arc<RwLock<Meter>>,
    transaction_id: u16,
    unit_id: u8,
) -> Option<Vec<u8>> {
    if request.len() < 12 {
        return create_exception_response(transaction_id, unit_id, 0x05, 0x03);
    }
    
    let address = u16::from_be_bytes([request[8], request[9]]);
    let value = u16::from_be_bytes([request[10], request[11]]);
    
    let coil_value = match value {
        0x0000 => false,
        0xFF00 => true,
        _ => return create_exception_response(transaction_id, unit_id, 0x05, 0x03),
    };
    
    let mut meter_lock = meter.write().await;
    if !meter_lock.set_coil_value(address, coil_value) {
        return create_exception_response(transaction_id, unit_id, 0x05, 0x02);
    }
    
    // Echo back the request as response for write single coil
    Some(request.to_vec())
}

async fn handle_write_single_register(
    request: &[u8],
    meter: &Arc<RwLock<Meter>>,
    transaction_id: u16,
    unit_id: u8,
) -> Option<Vec<u8>> {
    if request.len() < 12 {
        return create_exception_response(transaction_id, unit_id, 0x06, 0x03);
    }
    
    let address = u16::from_be_bytes([request[8], request[9]]);
    let value = u16::from_be_bytes([request[10], request[11]]);
    
    let mut meter_lock = meter.write().await;
    if !meter_lock.set_register_value(address, value) {
        return create_exception_response(transaction_id, unit_id, 0x06, 0x02);
    }
    
    // Echo back the request as response for write single register
    Some(request.to_vec())
}

fn create_exception_response(
    transaction_id: u16,
    unit_id: u8,
    function_code: u8,
    exception_code: u8,
) -> Option<Vec<u8>> {
    let mut response = Vec::new();
    response.extend_from_slice(&transaction_id.to_be_bytes());
    response.extend_from_slice(&0u16.to_be_bytes()); // Protocol ID
    response.extend_from_slice(&3u16.to_be_bytes()); // Length
    response.push(unit_id);
    response.push(function_code | 0x80); // Exception function code
    response.push(exception_code);
    
    Some(response)
}
