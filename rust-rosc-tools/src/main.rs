use std::io;
use scanpw::scanpw;
use reqwest::Client;
use serde::Serialize;
use std::error::Error;
use serde_json::Value;

pub async fn fetch_post<B: Serialize>(
    server_host: &str,
    endpoint: &str,
    port: u16,
    body: &B,
) -> Result<String, Box<dyn Error>> {
    // Build URL, allowing the endpoint to be provided with or without leading slash
    let endpoint: String = if endpoint.starts_with('/') {
        endpoint.to_string()
    } else {
        format!("/{}", endpoint)
    };
    let url: String = format!("{}:{}{}", server_host, port, endpoint);

    let client: Client = Client::new();

    let response_text = client
        .post(&url)
        .json(body)        // sets Content-Type: application/json and serializes the body
        .send()
        .await? // convert HTTP errors to Err so callers see non-2xx as Err
        .text()
        .await?;

    Ok(response_text)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Hello, world!");
    let mut session_id: String = String::new();
    let mut server_host = "https://localhost".to_owned();
    let mut port: u16 = 5912;
    loop {
        let mut command: String = String::new();
        io::stdin()
            .read_line(&mut command)
            .expect("Something went wrong");
        match command.trim() {
            "login" => {
                print!("Enter a username: ");
                let mut username: String = String::new();
                io::stdin()
                    .read_line(&mut username)
                    .expect("Something went wrong");
                let password: String = scanpw!("Enter a password: ");
                
                #[derive(Serialize)]
                struct LoginPayload {
                    username: String,
                    password: String
                }
                let payload: LoginPayload = LoginPayload {
                    username: username,
                    password: password,
                };
                
                let resp: String = fetch_post(&server_host, "/login", port, &payload).await?;
                let parsed: Value = serde_json::from_str(&resp)?;
                
                if parsed["success"].as_bool().unwrap_or(false) {
                    session_id = parsed["newSessionId"].as_str().unwrap_or("").to_owned();
                    println!("Successfully logged in")
                } else {
                    println!("{}",resp);
                }
            }
            
            "host" => {
                print!("Enter the hostname of the server without the port: ");
                io::stdin().read_line(&mut server_host).expect("Error reading line");
                print!("Enter the port: ");
                let mut str_port: String = String::new();
                io::stdin().read_line(&mut str_port).expect("Error reading line");
                if str_port != "".to_owned() {
                    match str_port.parse::<u16>() {
                        Ok(num) => {
                            port = num;
                        }
                        Err(_e) => {}
                    };
                }
            }
            
            "exit" => {
                break;
            }
            
            other => {
                println!("Unknown command {}", other)
            }
        }
    }
    
    Ok(())
}
