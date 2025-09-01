#[cfg(test)]
mod tests {
    use crate::{get_version, get_yaml_settings};
    use std::env;

    #[test]
    fn test_parse_current_fc_settings() {
        // 此测试验证当前的fc_settings.yaml是否能正确解析
        let result = get_yaml_settings("../fc_settings.yaml");

        match result {
            Ok(settings) => {
                println!("成功解析配置文件");
                println!("摘要生成启用: {}", settings.generate_summary.enabled);
                println!("提供商: {}", settings.generate_summary.provider);

                // 验证基本结构
                assert!(!settings.generate_summary.provider.is_empty());

                if settings.generate_summary.provider == "gemini" {
                    assert!(settings.generate_summary.gemini.is_some());
                    let gemini_config = settings.generate_summary.gemini.unwrap();
                    assert!(!gemini_config.models.is_empty());
                    println!("Gemini模型配置: {:?}", gemini_config.models);
                }

                if settings.generate_summary.provider == "siliconflow" {
                    assert!(settings.generate_summary.siliconflow.is_some());
                    let siliconflow_config = settings.generate_summary.siliconflow.unwrap();
                    assert!(!siliconflow_config.models.is_empty());
                    println!("SiliconFlow模型配置: {:?}", siliconflow_config.models);
                }
            }
            Err(e) => {
                panic!("解析配置文件失败: {e}");
            }
        }
    }

    #[test]
    fn test_provider_config_structure() {
        // 测试提供商配置结构的合理性
        let yaml_content = r#"
LINK:
  - link: "test"
    theme: "test"
SETTINGS_FRIENDS_LINKS:
  enable: false
  json_api_or_path: ""
  list: []
BLOCK_SITE: []
BLOCK_SITE_REVERSE: false
MAX_POSTS_NUM: 100
OUTDATE_CLEAN: 30
DATABASE: "sqlite"
DEPLOY_TYPE: "github"
SIMPLE_MODE: false
CRON: "0 0 */6 * *"
GENERATE_SUMMARY: {
  enabled: true,
  provider: "all",
  max_concurrent: 3,
  wait_on_rate_limit: true,
  max_chars: 8000,
  gemini: {
    models: ["gemini-2.5-flash", "gemini-2.5-pro"]
  },
  siliconflow: {
    models: ["THUDM/GLM-4.1V-9B-Thinking", "Qwen/Qwen3-8B", "THUDM/glm-4-9b-chat"]
  }
}
"#;

        let settings: data_structures::config::Settings =
            serde_yaml::from_str(yaml_content).unwrap();

        assert_eq!(settings.generate_summary.provider, "all");
        assert!(settings.generate_summary.enabled);

        // 验证两个提供商的配置都存在
        assert!(settings.generate_summary.gemini.is_some());
        assert!(settings.generate_summary.siliconflow.is_some());

        let gemini_config = settings.generate_summary.gemini.unwrap();
        assert_eq!(gemini_config.models.len(), 2);

        let siliconflow_config = settings.generate_summary.siliconflow.unwrap();
        assert_eq!(siliconflow_config.models.len(), 3);
    }

    #[test]
    fn test_get_version_basic_functionality() {
        // 测试基本功能：get_version 总是返回一个有效的版本号
        let version_response = get_version();

        // 验证返回的版本不为空
        assert!(!version_response.version.is_empty());

        // 验证版本格式（可能是 x.y.z 或者其他格式）
        let version_parts: Vec<&str> = version_response.version.split('.').collect();
        assert!(!version_parts.is_empty());
    }

    #[test]
    fn test_get_version_environment_variable_support() {
        // 保存原始环境变量
        let original_version = env::var("VERSION").ok();

        // 测试 VERSION 环境变量（手动覆盖编译时版本）
        unsafe {
            env::set_var("VERSION", "3.2.1");
        }

        let version_response = get_version();
        assert_eq!(version_response.version, "3.2.1");

        // 测试默认编译时版本（VERSION 环境变量不存在时）
        unsafe {
            env::remove_var("VERSION");
        }

        let version_response = get_version();
        // 应该返回编译时的版本号（来自 env!("CARGO_PKG_VERSION")）
        assert_eq!(version_response.version, env!("CARGO_PKG_VERSION"));

        // 恢复原始环境变量
        unsafe {
            if let Some(val) = original_version {
                env::set_var("VERSION", val);
            } else {
                env::remove_var("VERSION");
            }
        }
    }

    #[test]
    fn test_version_response_structure() {
        // 测试 VersionResponse 结构体的基本功能
        let version_response = get_version();

        // 验证返回的是 VersionResponse 结构体
        assert!(!version_response.version.is_empty());

        // 测试 VersionResponse::new 方法
        let manual_response =
            data_structures::version::VersionResponse::new("test-version".to_string());
        assert_eq!(manual_response.version, "test-version");

        // 测试 Clone 和 PartialEq traits
        let cloned_response = manual_response.clone();
        assert_eq!(manual_response, cloned_response);
    }
}
