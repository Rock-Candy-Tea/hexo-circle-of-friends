# 友链朋友圈

你是否经常烦恼于友链过多但没有时间浏览？那么友链朋友圈将解决这一痛点。你可以随时获取友链网站的更新内容，并了解友链的活跃情况。

部署教程：[文档](https://fcircle-doc.js.cool/) | [备用地址](https://fcircle-doc.is-a.dev/)

⭐从4.1.3版本开始，一定要在配置项中配置友链页和获取策略
```
目前 release 4.3.1 版本：
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
- 新增友链获取策略的common规则
- 新增api方式的配置项友链
- 将额外友链页和环境变量友链统一为LINK，在配置文件中配置

bug修复和改动：
- wordpress类型博客的时间格式问题
- butterfly主题友链页解析不再抓取背景图片了
- 修复了github和gitee对volantis主题的友链获取
- 屏蔽站点现在不计入失联数
- 修复了sakura主题和nexmoe主题偶尔报错的问题
- 现在可以获取Yun主题的外置JSON友链
- 优化了启动项配置
- feed订阅解析更加精准了
- 解决了docker和server定时任务运行爬虫报错的问题
- 文章超出当前时间的判断，逻辑优化与代码格式化
- 移除bs4依赖
- 移除旧订阅规则解析
- 修复butterfly的时间获取
- 额外友链页也可以配置获取策略
- 修复过期文章清除不生效的问题，解决mongodb空插入报错问题
```

