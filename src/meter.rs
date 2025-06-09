use rand::Rng;
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Copy)]
pub enum MeterType {
    Electric,
}

impl MeterType {
    #[allow(dead_code)]
    pub fn from_str(s: &str) -> Result<Self, String> {
        match s.to_lowercase().as_str() {
            "electric" => Ok(MeterType::Electric),
            _ => Err(format!("Unknown meter type: {}", s)),
        }
    }
}

pub struct Meter {
    pub meter_type: MeterType,
    pub registers: [u16; 200],
    pub coils: [bool; 100],
    last_update: Instant,

    // Electric meter specific
    cumulative_consumption: f64, // kWh
    base_power: f64,             // W
    voltage_l1: f64,             // V
    voltage_l2: f64,             // V
    voltage_l3: f64,             // V
    current_l1: f64,             // A
    current_l2: f64,             // A
    current_l3: f64,             // A
    frequency: f64,              // Hz
    power_factor: f64,           // 0-1
}

impl Meter {
    pub fn new(meter_type: MeterType) -> Self {
        let mut meter = Meter {
            meter_type,
            registers: [0; 200],
            coils: [false; 100],
            last_update: Instant::now(),
            cumulative_consumption: 1234.56,
            base_power: 5000.0,
            voltage_l1: 230.0,
            voltage_l2: 230.0,
            voltage_l3: 230.0,
            current_l1: 15.0,
            current_l2: 15.0,
            current_l3: 15.0,
            frequency: 50.0,
            power_factor: 0.95,
        };

        meter.initialize_coils();
        meter.update_registers();
        meter
    }

    fn initialize_coils(&mut self) {
        self.coils[0] = true; // Meter online
        self.coils[1] = true; // No alarms
        self.coils[2] = true; // Communication OK
    }

    pub fn update(&mut self) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_update);

        if elapsed >= Duration::from_secs(1) {
            self.update_readings(elapsed);
            self.update_registers();
            self.last_update = now;
        }
    }

    fn update_readings(&mut self, elapsed: Duration) {
        let mut rng = rand::thread_rng();
        let elapsed_hours = elapsed.as_secs_f64() / 3600.0;

        // Update electrical readings with realistic variations
        let power_variation = rng.gen_range(-0.1..0.1);
        let current_power = self.base_power * (1.0 + power_variation);

        // Update cumulative consumption
        self.cumulative_consumption += current_power * elapsed_hours / 1000.0; // Convert W to kWh

        // Update voltage (slight variations around 230V)
        self.voltage_l1 = 230.0 + rng.gen_range(-5.0..5.0);
        self.voltage_l2 = 230.0 + rng.gen_range(-5.0..5.0);
        self.voltage_l3 = 230.0 + rng.gen_range(-5.0..5.0);

        // Update current based on power and voltage
        self.current_l1 = current_power / (3.0 * self.voltage_l1 * self.power_factor);
        self.current_l2 = current_power / (3.0 * self.voltage_l2 * self.power_factor);
        self.current_l3 = current_power / (3.0 * self.voltage_l3 * self.power_factor);

        // Frequency variation around 50Hz
        self.frequency = 50.0 + rng.gen_range(-0.1..0.1);

        // Power factor variation
        self.power_factor = 0.95 + rng.gen_range(-0.05..0.05);
        if self.power_factor > 1.0 {
            self.power_factor = 1.0;
        }
        if self.power_factor < 0.8 {
            self.power_factor = 0.8;
        }
    }

    fn update_registers(&mut self) {
        // Common registers (0-9)
        let consumption_scaled = (self.cumulative_consumption * 100.0) as u32;
        self.registers[0] = (consumption_scaled & 0xFFFF) as u16; // Low word
        self.registers[1] = ((consumption_scaled >> 16) & 0xFFFF) as u16; // High word

        let power_scaled = (self.base_power * 10.0) as u32;
        self.registers[2] = (power_scaled & 0xFFFF) as u16; // Low word
        self.registers[3] = ((power_scaled >> 16) & 0xFFFF) as u16; // High word

        // Electric meter specific registers (10-17)
        self.registers[10] = (self.voltage_l1 * 10.0) as u16; // V × 10
        self.registers[11] = (self.voltage_l2 * 10.0) as u16; // V × 10
        self.registers[12] = (self.voltage_l3 * 10.0) as u16; // V × 10
        self.registers[13] = (self.current_l1 * 100.0) as u16; // A × 100
        self.registers[14] = (self.current_l2 * 100.0) as u16; // A × 100
        self.registers[15] = (self.current_l3 * 100.0) as u16; // A × 100
        self.registers[16] = (self.frequency * 100.0) as u16; // Hz × 100
        self.registers[17] = (self.power_factor * 1000.0) as u16; // × 1000

        // Status registers (100-101)
        self.registers[100] = if self.coils[0] { 1 } else { 0 }; // Online status
        self.registers[101] = self.meter_type as u16; // Meter type
    }

    pub fn get_register_value(&self, address: u16) -> u16 {
        if address < self.registers.len() as u16 {
            self.registers[address as usize]
        } else {
            0
        }
    }

    pub fn get_coil_value(&self, address: u16) -> bool {
        if address < self.coils.len() as u16 {
            self.coils[address as usize]
        } else {
            false
        }
    }

    pub fn set_coil_value(&mut self, address: u16, value: bool) -> bool {
        if address < self.coils.len() as u16 {
            match address {
                10 => {
                    // Reset command
                    if value {
                        self.cumulative_consumption = 0.0;
                        println!("Meter reset command received");
                    }
                    true
                }
                _ => {
                    self.coils[address as usize] = value;
                    true
                }
            }
        } else {
            false
        }
    }

    pub fn set_register_value(&mut self, address: u16, value: u16) -> bool {
        if address < self.registers.len() as u16 {
            self.registers[address as usize] = value;
            true
        } else {
            false
        }
    }
}
