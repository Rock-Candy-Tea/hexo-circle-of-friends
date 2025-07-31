#[cfg(test)]
mod tests {
    use crate::get_yaml_settings;

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
}
