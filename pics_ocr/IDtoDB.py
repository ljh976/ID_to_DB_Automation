# Import required packages
import numpy as np
import cv2 
import pytesseract 
import mysql.connector
import PIL.Image

#connect to mysql
def createDB():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
    )
    mycursor = mydb.cursor()
    try:
        sql = "CREATE DATABASE mydb"
        mycursor.execute(sql)
    except:
        print("db already exists")
    finally:    
        mydb.close()
    

def connectDB():
    #check if db exists
    createDB()
    
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        database="mydb"
    )
    
    return mydb

def createTable(mydb):                     
    #check if table exists
    mycursor = mydb.cursor()

    try:
        sql = ("CREATE TABLE students (system_id INT AUTO_INCREMENT primary key NOT NULL, firstName VARCHAR(255), "
       "middleName VARCHAR(255), lastName VARCHAR(255), uid VARCHAR(10), "
       "facePic BLOB)")
        mycursor.execute(sql)
    except:
        print("table already exsits")
            
        
def insertToMySQL(firstName, middleName, lastName, uid, facePic):
    mydb = connectDB()
    mycursor = mydb.cursor()    
    createTable(mydb)

    sql = "INSERT INTO students (firstName, middleName, lastName, uid, facePic) VALUES (%s, %s, %s, %s, %s)"
    val = (firstName, middleName, lastName, uid, facePic)
    
    print(firstName)
    print(middleName)
    print(lastName)
    print(uid)
    
    mycursor.execute(sql, val)
    #commit the changes. MUST!
    mydb.commit()
    
    print("Data submitted.")
    #close db connection
    mydb.close()
    
    

def myOCR():
    # Mention the installed location of Tesseract-OCR in your system 
    pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
    
    # Load the cascade for face
    face_cascade = cv2.CascadeClassifier('xmls/haarcascade_frontalface_default.xml')
    
    #change your file name here
    fileName = "2_id(censored).png"
    # Read image from which text needs to be extracted 
    img = 0
    try:
        img = cv2.imread(fileName)
    except:
        print("No file exists")
    
    #img = cv2.imread(fileName) 
    
    # Preprocessing the image starts 
    # Convert the image to gray scale 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    
    #detect face
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    # Draw rectangle around the faces
    croppedFace = []
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x-50, y-50), (x+w+100, y+h+100), (255, 0, 0), 2)
        croppedFace = img[y - 50:y + h + 100, x - 50:x + w + 100] 
    # Display the output
    
    cv2.imwrite('face.jpg', croppedFace)

    # Performing OTSU threshold 
    ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV) 
      
    # Decide structure shape and kernel size.  
    # Kernel size increases or decreases the area  
    # e.g. (10,10) will detect each words
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18)) 
      
    # Appplying dilation on the threshold image 
    dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1) 
      
    # Finding contours 
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,  
                                                     cv2.CHAIN_APPROX_NONE) 
      
    # Creating a copy of image 
    im2 = img.copy() 
      
    
    #personal info from id card
    #university id#
    uid = 0
    lastName = ""
    middleName = ""
    firstName = ""
    nameArr = []
    
    # Looping through the identified contours 
    # Then rectangular part is cropped and passed on 
    # to pytesseract for extracting text from it 
    # Extracted text is then written into the text file 
    for cnt in contours: 
        x, y, w, h = cv2.boundingRect(cnt) 
          
        # Drawing a rectangle on copied image 
        rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2) 
          
        # Cropping the text block for giving input to OCR 
        cropped = im2[y:y + h, x:x + w] 
          
        # Apply OCR on the cropped image 
        text = pytesseract.image_to_string(cropped) 
        if len(text) == 5 and text.isdigit(): #uid is 9 digit integer.
            uid = text
        elif (text != "Issue Date:"):
            if len(text.split()) > 1:
                nameArr = text.split()
                if len(nameArr) > 2: #in case the name contains middle name
                    firstName = nameArr[0]
                    middleName = nameArr[1]
                    lastName = nameArr[2]
                else:
                    firstName = nameArr[0]
                    lastName = nameArr[1]
    #read the jpg file from above
    facePic = open("face.jpg", 'rb').read()
    print (uid)
    print (nameArr)
    print (firstName)
    print (lastName)
    
    
    
    #insert results to the db
    insertToMySQL(firstName, middleName, lastName, uid, facePic)
    
    
    #check if the image is stored well
    mydb = connectDB()
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM students")
    myresult = mycursor.fetchall()
    count = 0
    for x in myresult:
        filename = "{}_{}_{}_{}.jpg".format(x[0], x[1], x[3], x[4])
        with open(filename, 'wb') as file:
            file.write(x[5]) 
        count += 1
    #disconnect db
    mydb.close()
myOCR()
