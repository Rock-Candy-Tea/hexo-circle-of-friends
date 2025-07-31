use api::{create_mongodb_app, create_mysql_app, create_sqlite_app};
use tools::init_tracing;
use tracing::{error, info};

#[tokio::main]
async fn main() {
    // 首先检查是否请求帮助
    if std::env::args().any(|arg| arg == "--help" || arg == "-h") {
        print_help();
        return;
    }

    let fc_settings = tools::get_yaml_settings("./fc_settings.yaml").unwrap();
    let _guard = init_tracing("fcircle_api", None);

    // 解析命令行参数获取端口号，默认为8000
    let port = parse_port_from_args().unwrap_or(8000);

    // 验证端口范围
    if !is_valid_port(port) {
        error!(
            "Invalid port number: {}. Port must be between 1 and 65535.",
            port
        );
        return;
    }

    let app = match fc_settings.database.as_str() {
        "sqlite" => create_sqlite_app("data.db").await,
        "mysql" => {
            // get mysql conn pool
            let mysqlconnstr = match tools::get_env_var("MYSQL_URI") {
                Ok(mysqlconnstr) => mysqlconnstr,
                Err(e) => {
                    error!("{}", e);
                    return;
                }
            };
            create_mysql_app(&mysqlconnstr).await
        }
        "mongodb" => {
            let mongodburi = match tools::get_env_var("MONGODB_URI") {
                Ok(mongodburi) => mongodburi,
                Err(e) => {
                    error!("{}", e);
                    return;
                }
            };
            create_mongodb_app(&mongodburi).await
        }
        _ => return,
    };

    // 在指定端口上启动服务器
    let bind_addr = format!("0.0.0.0:{port}");
    info!("Starting server on {}", bind_addr);

    let listener = match tokio::net::TcpListener::bind(&bind_addr).await {
        Ok(listener) => listener,
        Err(e) => {
            error!("Failed to bind to {}: {}", bind_addr, e);
            if e.kind() == std::io::ErrorKind::AddrInUse {
                error!(
                    "Port {} is already in use. Please choose a different port.",
                    port
                );
            }
            return;
        }
    };

    info!("Server successfully started on {}", bind_addr);

    if let Err(e) = axum::serve(listener, app).await {
        error!("Server error: {}", e);
    }
}

/// 从命令行参数解析端口号
/// 支持的格式:
/// - `./program 8080` (直接指定端口号)
/// - `./program --port 8080` (使用--port参数)
/// - `./program -p 8080` (使用-p参数)
fn parse_port_from_args() -> Option<u16> {
    let args: Vec<String> = std::env::args().collect();

    // 如果只有一个参数（程序名），返回None使用默认端口
    if args.len() == 1 {
        return None;
    }

    // 检查各种参数格式
    for (i, arg) in args.iter().enumerate() {
        match arg.as_str() {
            "--port" | "-p" => {
                // 下一个参数应该是端口号
                if i + 1 < args.len()
                    && let Ok(port) = args[i + 1].parse::<u16>()
                {
                    return Some(port);
                }
            }
            _ => {
                // 如果是第二个参数且是数字，直接当作端口号
                if i == 1
                    && let Ok(port) = arg.parse::<u16>()
                {
                    return Some(port);
                }
            }
        }
    }

    None
}

/// 验证端口号是否有效
fn is_valid_port(port: u16) -> bool {
    port > 0 // u16类型已经限制在0-65535范围内
}

/// 打印帮助信息
fn print_help() {
    println!("Hexo Circle of Friends API Server");
    println!();
    println!("用法:");
    println!("  fcircle_api [选项] [端口号]");
    println!();
    println!("选项:");
    println!("  -p, --port <端口号>     指定服务器监听端口 (默认: 8000)");
    println!("  -h, --help              显示此帮助信息");
    println!();
    println!("示例:");
    println!("  fcircle_api              # 使用默认端口 8000");
    println!("  fcircle_api 3000         # 监听端口 3000");
    println!("  fcircle_api --port 9090  # 监听端口 9090");
    println!("  fcircle_api -p 8080      # 监听端口 8080");
}
