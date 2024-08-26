echo "Start script"

(cd D:/Toan/Python/AutoSubCodePTIT && docker-compose up -d)
(cd D:/Toan/Python/AutoSubCodePTIT/app/APIs && uvicorn main:app --reload &)
(cd D:/Toan/Python/AutoSubCodePTIT/app && python puplisher.py &)
(cd D:/Toan/Python/AutoSubCodePTIT/app && python subcriber.py &)
(cd D:/Toan/Python/AutoSubCodePTIT/app && python auto.py &)

echo "End script"
