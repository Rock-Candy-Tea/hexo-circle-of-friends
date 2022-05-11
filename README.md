# 友链朋友圈

你是否经常烦恼于友链过多但没有时间浏览？那么友链朋友圈将解决这一痛点。你可以随时获取友链网站的更新内容，并了解友链的活跃情况。

部署教程：[文档](https://fcircle-doc.js.cool/) | [备用地址](https://fcircle-doc.is-a.dev/)

```
4.3.2 dev版本：
- 支持 gitee 和 github 上的 issuse 友链获取
- 支持butterfly、volantis、matery、sakura、fluid、nexmoe、Yun、stun、stellar、next主题的友链和文章获取
- 支持feed订阅规则，如atom、rss等规则（支持wordpress类型的博客）
- 支持自定义订阅后缀
- 支持站点屏蔽
- 支持按照更新时间和创建时间排序
- 支持未适配的hexo主题和非hexo用户使用，在配置项选择开启配置项友链
- 额外的友链页同时爬取
- 支持添加HTTP代理
- 多种数据存储，提供leancloud,mysql,sqlite,mongodb存储方式
- 多种方式部署，提供github,server,docker部署方式
- 将api整合到主仓库
- 新增友链获取策略的多种common规则
- 新增api方式的配置项友链
- 将额外友链页和环境变量友链统一为LINK，在配置文件中配置
- 提供一个简单的快速部署脚本

相较上版本的bug修复和改动：
- 修复了mysqlapi的连接问题
- 添加mongodb workflow
- 修复leancloud api在created规则下报错
- 修复mongodb插入数据报错问题
- 解决请求文章时domain不规则的报错
- 更新requirements依赖库
- randomfriend和randompost两个接口支持随机N篇功能
```

