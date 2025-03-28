from flask import Flask, render_template, jsonify, request, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash  
from flask_session import Session 
from flask_cors import CORS  

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS

# ✅ Add a SECRET_KEY (Set this to a secure random string)
app.config['SECRET_KEY'] = 'your_super_secret_key'  # Change this to a strong, unique key

# ✅ Configure Flask session
app.config['SESSION_TYPE'] = 'filesystem'  # Stores session data in the file system
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Adds an extra layer of security
Session(app)  # Initialize Flask-Session

# ✅ Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="dbms"
)
cursor = conn.cursor()

# ✅ Create table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        password VARCHAR(255),
        contact VARCHAR(20),
        gender VARCHAR(10),
        address VARCHAR(255),
        city VARCHAR(100),
        district VARCHAR(100),
        state VARCHAR(100),
        pincode VARCHAR(10)
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        email VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        password VARCHAR(255)
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS emp (
        email VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        password VARCHAR(255),
        contact VARCHAR(20),
        gender VARCHAR(10),
        address VARCHAR(255),
        city VARCHAR(100),
        district VARCHAR(100),
        state VARCHAR(100),
        pincode VARCHAR(10),
        salary varchar(225)
    )
''')
conn.commit()

cursor.execute( """
CREATE TABLE IF NOT EXISTS products (
    id INT(11) NOT NULL AUTO_INCREMENT,
    receiver_email VARCHAR(255) NOT NULL,
    receiver_name VARCHAR(255) NOT NULL,
    receiver_contact VARCHAR(20) NOT NULL,
    receiver_address TEXT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    pickup_date DATE NOT NULL,
    delivery_date DATE NOT NULL,
    product_image VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sender VARCHAR(225) NULL,
    status VARCHAR(15) NULL,
    incharge VARCHAR(225) NULL,
    get_date_time DATETIME NULL,
    set_date_time DATETIME NULL,
    PRIMARY KEY (id)
);
""")
conn.commit()

@app.route('/get_user_data', methods=['POST'])
def get_user_data():
    data = request.json
    user_email = data.get('email')

    if not user_email:
        return jsonify({"error": "Email is required"}), 400



    try:
        # Fetch user details
        cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Fetch sent products
        cursor.execute("SELECT * FROM products WHERE sender = %s", (user_email,))
        sent_products = cursor.fetchall()

        print(user)
        print(sent_products)

        return jsonify({"user": user, "sent_products": sent_products})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/storeProduct', methods=['POST'])
def store_product():
    try:
        
        
        receiver_email = request.form.get('receiverEmail')
        receiver_name = request.form.get('receiverName')
        receiver_contact = request.form.get('receiverContact')
        receiver_address = request.form.get('receiverAddress')
        product_name = request.form.get('productName')
        pickup_date = request.form.get('pickupDate')
        delivery_date = request.form.get('deliveryDate')
        sender = request.form.get('email')
        

        if not (receiver_email and receiver_name and receiver_contact and receiver_address and product_name and pickup_date and delivery_date):
            return jsonify({"error": "All fields are required"}), 400


        query = '''INSERT INTO products 
                   (receiver_email, receiver_name, receiver_contact, receiver_address, 
                   product_name, pickup_date, delivery_date,sender) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s,%s)'''
        
        values = (receiver_email, receiver_name, receiver_contact, receiver_address, 
                  product_name, pickup_date, delivery_date,sender)

        cursor.execute(query, values)
        conn.commit()

        return jsonify({"message": "Product details saved successfully!"}), 201
    except Exception as e:
        print("Error:", str(e))  # Debugging
        return jsonify({"error": str(e)}), 500


@app.route('/get_products', methods=['GET'])
def get_products():
    cursor.execute("SELECT * FROM products WHERE status IS NULL")
    products = cursor.fetchall()
    return jsonify(products)

# Update product status


@app.route('/update_status', methods=['POST'])
def update_status():
    try:
        data = request.json
        print("Received Data:", data)  # Debugging

        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        product_id = data.get("id")
        status = data.get("status")
        incharge = data.get("incharge")

        if not product_id or not status:
            return jsonify({"error": "Missing required fields"}), 400


        cursor = conn.cursor()

        # ✅ Execute query based on status
        if status == "Accepted" and incharge:
            cursor.execute("UPDATE products SET status=%s, incharge=%s WHERE id=%s", (status, incharge, product_id))
        else:
            cursor.execute("UPDATE products SET status=%s WHERE id=%s", (status, product_id))

        conn.commit()  # ✅ Commit changes
 # ✅ Close connection

        return jsonify({"message": f"Product {status} successfully!"})  # ✅ JSON Response

    except Exception as e:
        print("Error:", e)  # Logs the actual error
        return jsonify({"error": str(e)}), 500  # ✅ Return error response

# ✅ JSON Error Response

# ✅ Login Route
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json  
        email = data.get('email')
        password = data.get('password')

        cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            hashed_password = result[0]
            if check_password_hash(hashed_password, password):  
                session['email'] = email  # ✅ Now session will work
                return jsonify({"message": "Login successful!"}), 200
            else:
                return jsonify({"error": "Invalid password!"}), 401
        else:
            return jsonify({"error": "User not found!"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/userLogin.html')
def login_page():
    return render_template('userLogin.html')

# ✅ User Registration Route
@app.route('/users/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        hashed_password = generate_password_hash(data['password'])

        query = '''INSERT INTO users (name, email, password, contact, gender, address, city, district, state, pincode) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        values = (data['name'], data['email'], hashed_password, data['contact'], data['gender'],
                  data['address'], data['city'], data['district'], data['state'], data['pincode'])

        cursor.execute(query, values)
        conn.commit()

        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/adminlogin', methods=['POST'])
def login_admin():
    try:
        data = request.json  
        email = data.get('email')
        password = data.get('password')

        cursor.execute("SELECT password FROM admins WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            hashed_password = result[0]
            if check_password_hash(hashed_password, password):  
                session['email'] = email  # ✅ Now session will work
                return jsonify({"message": "Login successful!"}), 200
            else:
                return jsonify({"error": "Invalid password!"}), 401
        else:
            return jsonify({"error": "Admin not found!"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/register', methods=['POST'])
def register_admin():
    try:
        data = request.json
        hashed_password = generate_password_hash(data['password'])

        query = '''INSERT INTO admins (name, email, password) 
                   VALUES (%s, %s, %s)'''
        values = (data['name'], data['email'], hashed_password)

        cursor.execute(query, values)
        conn.commit()

        return jsonify({"message": "admin registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/emp/register', methods=['POST'])
def register_emp():
    try:
        data = request.json
        hashed_password = generate_password_hash(data['password'])

        query = '''INSERT INTO emp (name, email, password, contact, gender, address, city, district, state, pincode, salary) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)'''
        values = (data['name'], data['email'], hashed_password, data['contact'], data['gender'],
                  data['address'], data['city'], data['district'], data['state'], data['pincode'],data['salary'])

        cursor.execute(query, values)
        conn.commit()

        return jsonify({"message": "emp registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/emplogin', methods=['POST'])
def login_emp():
    try:
        data = request.json  
        email = data.get('email')
        password = data.get('password')

        cursor.execute("SELECT password FROM emp WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            hashed_password = result[0]
            if check_password_hash(hashed_password, password):  
                session['email'] = email  # ✅ Now session will work
                return jsonify({"message": "Login successful!"}), 200
            else:
                return jsonify({"error": "Invalid password!"}), 401
        else:
            return jsonify({"error": "emp not found!"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Fetch Employees
@app.route('/get_employees', methods=['GET'])
def get_employees():
    cursor.execute("SELECT * FROM emp")
    employees = cursor.fetchall()
    return jsonify({"employees": employees})

# Delete Employee
@app.route('/delete_employee', methods=['POST'])
def delete_employee():
    data = request.json
    email = data.get("email")

    cursor.execute("DELETE FROM emp WHERE email = %s", (email,))
    conn.commit()

    return jsonify({"success": True})


@app.route('/get_product_date', methods=['POST'])
def get_product_by_date():
    try:
        data = request.json
        selected_date = data.get("date")

        if not selected_date:
            return jsonify({"error": "No date provided"}), 400



        # ✅ Query to find products with matching pickup or delivery date
        query_pickup = "SELECT product_name, receiver_name, receiver_contact FROM products WHERE pickup_date = %s"
        query_delivery = "SELECT product_name, receiver_name, receiver_contact FROM products WHERE delivery_date = %s"

        cursor.execute(query_pickup, (selected_date,))
        pickup_products = cursor.fetchall()

        cursor.execute(query_delivery, (selected_date,))
        delivery_products = cursor.fetchall()



        return jsonify({"pickup": pickup_products, "delivery": delivery_products})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    

@app.route('/get_product_set_get_date', methods=['POST'])
def get_product_by_set_get_date():
    try:
        data = request.json
        selected_date = data.get("date")
        email = data.get("email")

        if not selected_date:
            return jsonify({"error": "No date provided"}), 400



        # ✅ Query to find products with matching pickup or delivery date
        query_pickup = "SELECT product_name, receiver_name, receiver_contact FROM products WHERE date(get_date_time) = %s and incharge = %s"
        query_delivery = "SELECT product_name, receiver_name, receiver_contact FROM products WHERE left(set_date_time,10) = %s and incharge =%s"

        cursor.execute(query_pickup, (selected_date,email,))
        pickup_products = cursor.fetchall()

        cursor.execute(query_delivery, (selected_date,email,))
        delivery_products = cursor.fetchall()



        return jsonify({"get_date_time_products": pickup_products, "set_date_time_products": delivery_products})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_employee_products', methods=['POST'])
def get_employee_products():
    try:
        data = request.json
        email = data.get("email")

   

        query = """
        SELECT id, product_name, pickup_date, delivery_date, get_date_time, set_date_time
        FROM products WHERE incharge = %s AND set_date_time IS NULL
        """
        cursor.execute(query, (email,))
        products = cursor.fetchall()


        return jsonify(products)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/update_product_date', methods=['POST'])
def update_product_date():
    try:
        data = request.json
        product_id = data.get("product_id")
        date_time = data.get("date_time")
        action = data.get("action")

        if not product_id or not date_time or not action:
            return jsonify({"error": "Missing required fields"}), 400


        if action == "get":
            query = "UPDATE products SET get_date_time = %s WHERE id = %s"
        elif action == "set":
            query = "UPDATE products SET set_date_time = %s WHERE id = %s"
        else:
            return jsonify({"error": "Invalid action"}), 400

        cursor.execute(query, (date_time, product_id))
        conn.commit()


        return jsonify({"message": f"{action.capitalize()} Date Updated Successfully!"})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500



@app.route('/UserReg.html')
def user_registration():
    return render_template('UserReg.html')

@app.route('/userPage.html')
def user_page():
    return render_template('userPage.html')

@app.route('/profilePage.html')
def user_profile():
    return render_template('profilePage.html')

#profilePage.html
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/adminLogin.html')
def admin_login():
    return render_template('adminLogin.html')

@app.route('/adminReg.html')
def admin_reg():
    return render_template('adminReg.html')

@app.route('/adminPage.html')
def admin_page():
    return render_template('adminPage.html')

@app.route('/empLogin.html')
def emp_login():
    return render_template('empLogin.html')

@app.route('/empReg.html')
def emp_reg():
    return render_template('empReg.html')

@app.route('/empPage.html')
def emp_page():
    return render_template('empPage.html')

@app.route('/empList.html')
def emp_list():
    return render_template('empList.html')
@app.route('/addEmp.html')
def emp_add():
    return render_template('addEmp.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
#python d:\Mini_Projects\py_dbms\pycode.py