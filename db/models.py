from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Date, ForeignKey, DateTime, func
from db.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    phone = Column(String)
    full_name = Column(String)
    role = Column(String, default="employee")
    manager_id = Column(Integer, nullable=True)
    vacation_days_balance = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Новые поля анкеты
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    tg_username = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    car_info = Column(String, nullable=True)
    face_id_photo = Column(String, nullable=True)
    approval_status = Column(String, default="approved")

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) # vacation_paid, vacation_unpaid, income_cert, work_cert, sick_leave
    status = Column(String, default="pending") # pending, manager_approved, hr_approved, rejected, done
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    days_count = Column(Integer, nullable=True)
    comment = Column(String, nullable=True)
    hr_comment = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class FAQ(Base):
    __tablename__ = "faq"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String)
    answer = Column(String)