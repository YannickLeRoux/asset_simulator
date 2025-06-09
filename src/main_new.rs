use clap::{Arg, Command};
use log::info;
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{interval, Duration};

mod meter;
mod modbus_server;

use meter::{Meter, MeterType};
use modbus_server::ModbusServer;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    
    let matches = Command::new("Asset Simulator")
        .version("0.1.0")
        .about("Virtual electric meter simulator with Modbus support")
        .arg(
            Arg::new("port")
                .short('p')
                .long("port")
                .value_name("PORT")
                .help("Modbus TCP port")
                .default_value("5020"),
        )
        .arg(
            Arg::new("address")
                .short('a')
                .long("address")
                .value_name("ADDRESS")
                .help("Bind address")
                .default_value("127.0.0.1"),
        )
        .get_matches();

    let port: u16 = matches.get_one::<String>("port").unwrap().parse()?;
    let address = matches.get_one::<String>("address").unwrap();
    
    // Create electric meter
    let meter = Arc::new(RwLock::new(Meter::new(MeterType::Electric)));
    
    info!("Starting electric meter simulator...");
    info!("Modbus TCP server will start on {}:{}", address, port);
    
    // Clone meter for the update task
    let meter_clone = meter.clone();
    
    // Start meter update task
    tokio::spawn(async move {
        let mut meter = meter_clone;
        let mut interval = interval(Duration::from_millis(1000));
        
        loop {
            interval.tick().await;
            {
                let mut m = meter.write().await;
                m.update();
            }
        }
    });
    
    // Start Modbus server
    let modbus_server = ModbusServer::new(meter);
    modbus_server.start(address, port).await?;
    
    Ok(())
}
