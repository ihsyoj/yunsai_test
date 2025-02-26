启动方法(tmux中启动, 带日志)
```
export PYTHONPATH=.

CUR_TIME=$(TZ='Asia/Shanghai' date +%Y%m%d-%H%M%S)

LOG_DIR=qujing/log
mkdir -p ${LOG_DIR}
LOG_PATH=${LOG_DIR}/${CUR_TIME}.log

echo "Start service. Log path: ${LOG_PATH}"
CUDA_VISIBLE_DEVICES=0 python -m streamlit run qujing/demo.py --server.address 0.0.0.0 --server.port 6004 2>&1 | tee $LOG_PATH
```

直接启动
```
CUDA_VISIBLE_DEVICES=0 python -m streamlit run qujing/demo.py --server.address 0.0.0.0 --server.port 6004
```