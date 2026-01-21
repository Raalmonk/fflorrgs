# main.py
import uvicorn
import os

if __name__ == "__main__":
    # 确保设置了必要的环境变量 (和 debug 脚本一样)
    # 如果你在系统里设过了可以省略
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    
    # 填入你的 WCL 客户端 ID 和 Secret
    # os.environ["WCL_CLIENT_ID"] = "..."
    # os.environ["WCL_CLIENT_SECRET"] = "..."
    os.environ["WCL_CLIENT_ID"] = "a0e16bba-fba8-432d-a317-4a6a83d98728"
    os.environ["WCL_CLIENT_SECRET"] = "Rowpl4stVguifS4YJbzow1HCjh1g2uNuGNaFYRPk"
    # 启动 uvicorn 服务器
    # "lorrgs_api.app:app" 指向 lorrgs_api/app.py 里的 app 对象
    uvicorn.run("lorrgs_api.app:api", host="127.0.0.1", port=5000, reload=True)