
echo "Start script"

(cd D:/Toan/Python/AutoSubCodePTIT && docker-compose up -d)
(prefect server start)
(cd D:/Toan/Python/AutoSubCodePTIT/app && python puplisher.py &)
(cd D:/Toan/Python/AutoSubCodePTIT/app && python subcriber.py &)
(cd D:/Toan/Python/AutoSubCodePTIT/app/APIs && uvicorn main:app --reload &)

echo "End script"
