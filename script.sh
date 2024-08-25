echo "Start script"
(cd /mnt/d/Toan/Python/AutoSubCodePTIT/app && python puplisher.py &)

(cd /mnt/d/Toan/Python/AutoSubCodePTIT/app && python subcriber.py &)

(cd /mnt/d/Toan/Python/AutoSubCodePTIT/app/APIs && uvicorn main:app --reload &)

