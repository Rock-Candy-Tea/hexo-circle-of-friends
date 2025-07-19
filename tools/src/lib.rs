use chrono::{DateTime, FixedOffset, NaiveDateTime, TimeZone, Utc};
use data_structures::config;
use logroller::{Compression, LogRollerBuilder, Rotation, RotationAge};
pub use serde_yaml::Value;
use std::fs::File;
use std::io::{self};
use tracing::info;
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::{
    EnvFilter,
    fmt::{self, format},
    prelude::*,
};

#[allow(deprecated)]
pub fn init_tracing(logger_name: &str, filter_str: Option<&str>) -> WorkerGuard {
    // stdout和file同时输出，并设置不同的fmt
    // 输出划分为http和core两个文件，通过filter来实现 https://docs.rs/tracing-subscriber/latest/tracing_subscriber/layer/index.html
    let formmater_string = "%Y-%m-%d %H:%M:%S (%Z)".to_string();
    let timer = tracing_subscriber::fmt::time::ChronoLocal::new(formmater_string);
    // about timezone,see:https://github.com/tokio-rs/tracing/issues/3102
    let appender = LogRollerBuilder::new("./logs", &format!("{logger_name}.log"))
        .rotation(Rotation::AgeBased(RotationAge::Daily)) // Rotate daily
        .max_keep_files(7) // Keep a week's worth of logs
        .time_zone(logroller::TimeZone::Local) // Use local timezone
        .compression(Compression::Gzip) // Compress old logs
        .build()
        .unwrap();
    let stdout_layer = fmt::layer()
        .with_target(true)
        .with_level(true)
        .with_timer(timer.clone())
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .with_ansi(true)
        .compact();
    let (non_blocking, _guard) = tracing_appender::non_blocking(appender);

    let layer = fmt::layer()
        .with_target(true)
        .with_level(true)
        .with_thread_ids(true)
        .with_timer(timer.clone())
        .with_file(true)
        .with_line_number(true)
        .with_ansi(false)
        .fmt_fields(format::PrettyFields::new().with_ansi(false))
        .with_writer(non_blocking)
        .compact();
    // let filter = EnvFilter::new("trace,tower_http=trace,sqlx::query=info");
    let global_filter = if let Some(filter_str) = filter_str {
        EnvFilter::new(filter_str)
    } else {
        EnvFilter::new("trace")
    };
    tracing_subscriber::registry()
        .with(global_filter)
        .with(stdout_layer)
        .with(layer)
        .init();
    info!("Setup tracing success for {}", logger_name);
    _guard
}

/// 将时间结构转换为统一格式的字符串`%Y-%m-%d %H:%M:%S`，带时分秒
pub fn strptime_to_string_ymdhms<Tz: TimeZone>(strptime: DateTime<Tz>) -> String {
    strptime
        .fixed_offset()
        .format("%Y-%m-%d %H:%M:%S")
        .to_string()
}

/// 将时间结构转换为统一格式的字符串`%Y-%m-%d`，不带时分秒
pub fn strptime_to_string_ymd<Tz: TimeZone>(strptime: DateTime<Tz>) -> String {
    strptime.fixed_offset().format("%Y-%m-%d").to_string()
}

/// 将可能不标准的时间字符串转换为统一格式的字符串`%Y-%m-%d`，不带时分秒
pub fn strftime_to_string_ymd(strftime: &str) -> String {
    let fmts = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.000Z", // 2021-11-12T01:24:06.000Z
        "%Y年%m月%d日",           // xxxx年xx月xx日
    ];
    for fmt in fmts {
        if let Ok(v) = NaiveDateTime::parse_from_str(strftime, fmt) {
            return v.format("%Y-%m-%d").to_string();
        };
    }
    strptime_to_string_ymd(Utc::now().with_timezone(&FixedOffset::east_opt(8 * 60 * 60).unwrap()))
}

pub fn get_yaml(path: &str) -> io::Result<Value> {
    let config_file = File::open(path)?;
    match serde_yaml::from_reader(config_file) {
        Ok(config) => Ok(config),
        Err(err) => panic!("{}", err),
    }
}

pub fn get_yaml_settings(path: &str) -> io::Result<config::Settings> {
    let config_file = File::open(path)?;
    match serde_yaml::from_reader(config_file) {
        Ok(config) => Ok(config),
        Err(err) => panic!("{}", err),
    }
}

/// 获取环境变量，如果为空则返回错误
pub fn get_env_var(var_name: &str) -> Result<String, Box<dyn std::error::Error>> {
    dotenvy::dotenv_override()?;
    match dotenvy::var(var_name) {
        Ok(var) => {
            if var.is_empty() {
                Err(Box::new(std::io::Error::other(format!(
                    "{var_name} is not set",
                ))))
            } else {
                Ok(var)
            }
        }
        Err(_) => Err(Box::new(std::io::Error::other(format!(
            "{var_name} is not set",
        )))),
    }
}
