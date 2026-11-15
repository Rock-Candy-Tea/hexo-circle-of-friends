#[cfg(test)]
mod tests {
    use crate::config::*;

    fn make_config() -> GenerateSummaryConfig {
        GenerateSummaryConfig {
            enabled: true,
            max_concurrent: 3,
            wait_on_rate_limit: true,
            max_chars: 8000,
            providers: vec![ProviderConfig {
                name: "siliconflow".to_string(),
                base_url: "https://api.siliconflow.cn/v1".to_string(),
                api_key_env: "SILICONFLOW_API_KEY".to_string(),
                models: vec!["deepseek-ai/DeepSeek-V3.2".to_string()],
            }],
        }
    }

    #[test]
    fn test_generate_summary_config_deserialization() {
        let yaml_content = r#"
enabled: true
max_concurrent: 5
wait_on_rate_limit: false
max_chars: 10000
providers:
  - name: "siliconflow"
    base_url: "https://api.siliconflow.cn/v1"
    api_key_env: "SILICONFLOW_API_KEY"
    models: ["deepseek-ai/DeepSeek-V3.2", "Qwen/Qwen3.6-27B"]
  - name: "bigmodel"
    base_url: "https://open.bigmodel.cn/api/paas/v4"
    api_key_env: "BIGMODEL_API_KEY"
    models: ["glm-4.7"]
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.get_max_concurrent(), 5);
        assert!(!config.get_wait_on_rate_limit());
        assert_eq!(config.get_max_chars(), 10000);
        assert_eq!(config.get_chunk_size(), 5000); // 自动计算为一半

        assert_eq!(config.providers.len(), 2);

        let siliconflow = &config.providers[0];
        assert_eq!(siliconflow.name, "siliconflow");
        assert_eq!(siliconflow.base_url, "https://api.siliconflow.cn/v1");
        assert_eq!(siliconflow.api_key_env, "SILICONFLOW_API_KEY");
        assert_eq!(siliconflow.models.len(), 2);
        assert!(
            siliconflow
                .models
                .contains(&"deepseek-ai/DeepSeek-V3.2".to_string())
        );

        let bigmodel = &config.providers[1];
        assert_eq!(bigmodel.name, "bigmodel");
        assert_eq!(bigmodel.models.len(), 1);
        assert!(bigmodel.models.contains(&"glm-4.7".to_string()));
    }

    #[test]
    fn test_generate_summary_config_disabled() {
        let yaml_content = r#"
enabled: false
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
providers: []
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(!config.enabled);
        assert!(config.providers.is_empty());
    }

    #[test]
    fn test_generate_summary_config_serialization_roundtrip() {
        let config = make_config();

        let yaml_str = serde_yaml::to_string(&config).unwrap();

        // 验证可以重新解析且结果一致
        let parsed_config: GenerateSummaryConfig = serde_yaml::from_str(&yaml_str).unwrap();
        assert_eq!(parsed_config, config);
    }

    #[test]
    fn test_generate_summary_config_clone() {
        let original = make_config();

        let cloned = original.clone();

        assert_eq!(original.enabled, cloned.enabled);
        assert_eq!(original.providers, cloned.providers);
    }

    #[test]
    fn test_default_values() {
        let config = make_config();

        assert_eq!(config.get_max_concurrent(), 3);
        assert!(config.get_wait_on_rate_limit());
        assert_eq!(config.get_max_chars(), 8000);
        assert_eq!(config.get_chunk_size(), 4000);
        assert_eq!(config.get_retry_attempts(), 3);
        assert_eq!(config.get_rate_limit_delay(), 60);
    }

    #[test]
    fn test_custom_values() {
        let mut config = make_config();
        config.max_concurrent = 5;
        config.wait_on_rate_limit = false;
        config.max_chars = 12000;

        assert_eq!(config.get_max_concurrent(), 5);
        assert!(!config.get_wait_on_rate_limit());
        assert_eq!(config.get_max_chars(), 12000);
        assert_eq!(config.get_chunk_size(), 6000); // 自动计算为一半
    }

    #[test]
    fn test_generate_summary_config_dict_format() {
        // 测试大括号 dict/流式格式
        let yaml_content = r#"
enabled: true
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
providers: [
  { name: "siliconflow", base_url: "https://api.siliconflow.cn/v1", api_key_env: "SILICONFLOW_API_KEY", models: ["deepseek-ai/DeepSeek-V3.2"] }
]
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.providers.len(), 1);
        assert_eq!(config.providers[0].name, "siliconflow");
        assert_eq!(config.providers[0].models.len(), 1);
    }
}
