# 友链朋友圈

你是否经常烦恼于友链过多但没有时间浏览？那么友链朋友圈将解决这一痛点。你可以随时获取友链网站的更新内容，并了解友链的活跃情况。

部署教程：[文档](https://fcircle-doc.js.cool/) | [备用地址](https://fcircle-doc.is-a.dev/)

```
4.3.2 支持：
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

最近改动：
- 添加mongodb workflow
- randomfriend和randompost两个接口支持随机N篇功能
- 新增lostfriends接口，用于快速查询失联友链
- 修复leancloud过期文章清理不生效的问题
- 添加自定义日志信息
- 修复leancloud接口中统计的数量和实际数量不同的问题
- 修复leancloud接口中创建时间和更新时间颠倒问题
```

