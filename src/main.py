from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from src.auth import AuthService
from src.models import UserUpdate, UserCreate, UserDB, UserResponse
from src.database import engine, SessionLocal, Base

#Database table creation
Base.metadata.create_all(bind=engine)

app = FastAPI()
auth_service = AuthService()

#DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Endpoint testing
@app.get("/test-db", response_model=list[UserResponse])  #Resource model to list
def test_db(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()  #Get all users from DB
    if not users:
        raise HTTPException(status_code=404, detail="No users found in the database.")
    return users  #Returns users, if none then return 404 redirect

#Create a new user (C)
@app.post("/users/", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    #Can't register same user
    existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    #Protection
    hashed_password = auth_service.hash_password(user.password)

    #New user with a strong password
    new_user = UserDB(username=user.username, password=hashed_password)
    
    #Add to PostgreSQL database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(id=new_user.id, username=new_user.username)

#Read a user if it exists (R)
@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

#Update a user if it exists (U)
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    existing_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    #optional fields to update
    if user.username:
        existing_user.username = user.username
    if user.password:
        existing_user.password = auth_service.hash_password(user.password)  #new password
    if user.id:
        existing_user.id = user.id  #update the user id

    #Add to DB and refresh
    db.commit()
    db.refresh(existing_user)
    
    return existing_user

#Finally, Delete the user if requested by them (D)
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully."}

#Testing for login purposes
@app.post("/login/")
async def login(user: UserCreate, db: Session = Depends(get_db)):  #Ensure to use UserCreate here
    #Fetch user by username
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    
    #Verify again common practice in login services
    if db_user is None or not auth_service.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    return {"message": "Login successful", "username": db_user.username}  #Returns login success

#Collect all users displaying the db of them
@app.get("/users/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(UserDB).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

#For the current user to check themselves
@app.get("/users/me")
def read_users_me(current_user: str = Depends(auth_service.get_current_user)):
    return {"username": current_user}

