@echo off
echo 开始测试数据获取...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 安装必要的依赖包
echo 安装依赖包...
pip install pandas requests >nul 2>&1

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "data\index_quote" mkdir data\index_quote
if not exist "logs" mkdir logs

REM 运行测试
echo 运行数据获取测试...
python test_data_fetch.py

echo.
echo 测试完成！
pause