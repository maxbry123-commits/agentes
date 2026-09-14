# H-Pentest Frontend Dockerfile
FROM node:18-alpine

# 【国内加速】配置APK清华源（国外用户可注释以下3行）
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
# 【国内加速结束】

# 安装wget用于健康检查
RUN apk add --no-cache wget

# 设置工作目录（与本地一致）
WORKDIR /home/H-pentest/H-pentest/frontend

# 复制package.json
COPY package*.json ./

# 【国内加速】配置淘宝镜像（国外用户可注释以下2行）
RUN npm config set registry https://registry.npmmirror.com
# 【国内加速结束】

# 安装依赖（使用 ci 更快，如果没有 package-lock.json 则用 install）
RUN npm install --prefer-offline --no-audit --progress=false

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 5173

# 设置环境变量
ENV NODE_ENV=development

# 启动命令
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
