# 配置项说明

主要分为项目配置和环境变量配置。

## 项目配置

项目配置在仓库中的`/hexo_circle_of_friends/setting.py`文件：

请根据需要，修改其中的内容。

## 环境变量配置

### github部署

如果采用github部署方式，环境变量需要在你fork的仓库下创建`secert`，根据存储方式的不同，需要配置的环境变量也不同。

可以在`/.github/workflows/main.yml`文件中查看。

```yaml
env:
  # 在这里查看需要添加的secert
  # 通用配置
  STORAGE_TYPE: leancloud # 请修改为你的存储方式，默认为leancloud
  LINK: ${{ secrets.LINK }} # 必须，你的友链链接地址
  PROXY: ${{ secrets.PROXY }} # 可选，http代理
  # leancloud、mysql、sqlite配置三选一即可
  # leancloud配置
  APPID: ${{ secrets.APPID }}
  APPKEY: ${{ secrets.APPKEY }}
  # mysql配置
  MYSQL_USERNAME: ${{ secrets.MYSQL_USERNAME }} # 登录用户名
  MYSQL_PASSWORD: ${{ secrets.MYSQL_PASSWORD }} # 登录密码
  MYSQL_IP: ${{ secrets.MYSQL_IP }} # 数据库IP地址
  MYSQL_DB: ${{ secrets.MYSQL_DB }} # 要连接到的库的名称
  # sqlite配置，用于将db文件上传到github仓库
  GITHUB_NAME: ${{ secrets.GITHUB_NAME }} # 你的github昵称
  GITHUB_EMAIL: ${{ secrets.GITHUB_EMAIL }} # 你的github邮箱
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # github token
```

比如，如果使用sqlite，仓库需要添加的secert为：`LINK`，`GITHUB_NAME`，`GITHUB_EMAIL`，`GITHUB_TOKEN`。

### server部署

如果采用github部署方式，环境变量配置需要修改在`server.sh`文件。

### docker部署

如果采用github部署方式，环境变量配置需要修改`Dockerfile`文件。

## 配置示例

### github+sqlite

如果想使用github+sqlite数据库，修改`settings.py`文件：

```python
# 存储方式，可选项：leancloud，mysql, sqlite；默认为leancloud
DATABASE = "sqlite"

# 部署方式，可选项：github，server，docker；默认为github
DEPLOY_TYPE = "github"
```

修改`main.yml`文件：

```yaml
env:
  # 通用配置
  STORAGE_TYPE: sqlite # 如果不配置，默认为leancloud
```

添加secert：`LINK`，`GITHUB_NAME`，`GITHUB_EMAIL`，`GITHUB_TOKEN`

### docker+mysql

