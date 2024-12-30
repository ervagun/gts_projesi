import pyodbc
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime 

app = Flask(__name__)
app.secret_key = 'my_super_secret_key_123!'  # Flask uygulamanız için secret key tanımlayın

# SQL Server'a bağlanmak için bağlantı dizesi (Windows Authentication)
def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=LAPTOP-IFUDD3DE\SQLEXPRESS01;'  # SQL Server adresi
        'DATABASE=GTSProject;'  # Veritabanınızın adı
        'Trusted_Connection=yes;'  # Windows Authentication ile bağlanmak için
    )
    return conn

# Ana Sayfa
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ThesisID, Title, ThesisType, Year, Language, PageCount FROM Thesis')
    thesis = cursor.fetchall()  # Verileri çekiyoruz
    conn.close()
    return render_template('search_result.html', thesis=thesis)

# Add Data Sayfası
@app.route('/add_data')
def add_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # University, Institute, Author, SubjectTopic, SupervisorInfo, verilerini çekiyoruz
    # add data sayfasında add thesis içerisindeki seçilebilen alanların databaseden verilerini getirdiğimiz yer
    cursor.execute('SELECT UniversityID, Name FROM University')
    university = cursor.fetchall()

    cursor.execute('SELECT InstituteID, Name, UniversityID FROM Institute')
    institute = cursor.fetchall()

    cursor.execute('SELECT SupervisorID,FirstName,LastName FROM SupervisorInfo')
    supervisor= cursor.fetchall()

    cursor.execute('SELECT AuthorID, FirstName, LastName, AuthorType FROM Author')
    author = cursor.fetchall()
   
    cursor.execute('SELECT SubjectTopicID, TopicName FROM SubjectTopic')
    subjecttopic = cursor.fetchall()

    conn.close()

    # Verileri add_data.html sayfasına gönderiyoruz
    return render_template('add_data.html', university=university, institute=institute,supervisor=supervisor, author=author, subjecttopic=subjecttopic)

# add author
@app.route('/add_author', methods=['POST'])
def add_author():
    conn = get_db_connection()
    author_type = request.form.get('type')
    first_name = request.form.get('first_name')  # first name'i al
    last_name = request.form.get('last_name')    # last name'i al

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Author(AuthorType, FirstName, LastName) VALUES(?,?, ?)", (author_type, first_name, last_name,))
        conn.commit()
        return render_template('result.html', response="Author added successfully")
    
    except pyodbc.Error as e:
        return render_template('result.html', response=str(e), error=True)
    finally:
        conn.close() 

# add university
@app.route('/add_university', methods=['POST'])
def add_university():
    conn = get_db_connection()
    cursor = conn.cursor()
    name = request.form.get('name')
    city = request.form.get('city')
    country = request.form.get('country')
    year = request.form.get('year')
    try:
        cursor.execute("""
            INSERT INTO University([Name], [City], [Country], [EstablishedYear]) 
            VALUES(?, ?, ?, ?)
        """, (name, city, country, year))
        conn.commit()
        return render_template('result.html', response="University added successfully")

    except pyodbc.Error as e:
         return render_template('result.html', response=str(e), error=True)
       
    finally:
         conn.close() 

# add institute
@app.route('/add_institute', methods=['POST'])
def add_institute():
    conn = get_db_connection()
    cursor = conn.cursor()
    name = request.form.get('name')
    uni = request.form.get('uni')
    institute_type = request.form.get('institute_type') 
    year = request.form.get('year') 
    try:
        cursor.execute("""
            INSERT INTO Institute([Name], [UniversityID], [InstituteType], [EstablishedYear]) 
            VALUES (?, ?, ?, ?)
        """, (name, uni, institute_type, year))
        conn.commit()
        return render_template('result.html', response="Institute added successfully")
    except pyodbc.Error as e:
        return render_template('result.html', response=str(e), error=True)
    finally:
        conn.close()


# add topic
@app.route('/add_topic', methods=['POST'])
def add_topic():
    conn = get_db_connection()
    cursor = conn.cursor()
    name = request.form.get('name')
    # if topic already exists, return error
    cursor.execute("SELECT TopicName FROM SubjectTopic WHERE TopicName = ?", (name,))
    if cursor.fetchone():
        return render_template('result.html', response="Topic already exists.", error=True)
    try:
        cursor.execute("INSERT INTO SubjectTopic(TopicName) VALUES(?)", (name,))
        conn.commit()
        return render_template('result.html', response="Topic added successfully")
    except pyodbc.Error as e:
        return render_template('result.html', response=str(e), error=True)
    finally:
        conn.close()

# add thesis
@app.route('/add_thesis', methods=['POST'])
def add_thesis():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

         # Kullanıcıdan gelen verileri al
        
        title = request.form.get('title')
        abstract = request.form.get('abstract')
        author_id = int(request.form.get('author'))
        year = int(request.form.get('year'))
        thesis_type = request.form.get('type')
        university_id = int(request.form.get('uni'))
        institute_id = int(request.form.get('ins'))
        num_pages = int(request.form.get('num_pages'))
        language = request.form.get('language')

        # COsupervisor var mı yok mu kontrol
        supervisors = [int(s) for s in request.form.getlist('supervisors')]

        if request.form.getlist('cosupervisors') == ['']:
            cosupervisors = []
        else:
            cosupervisors = [int(cs) for cs in request.form.getlist('cosupervisors')]


        topics = [int(t) for t in request.form.get('topics')]
        keywords = [kw.strip() for kw in request.form.get('keywords', '').split(',') if kw.strip()]
        submission_date = datetime.now().strftime('%Y-%m-%d')

        # Validasyonlar
        if not supervisors:
            return render_template('result.html', response="At least one supervisor is required.", error=True)
        if not topics:
            return render_template('result.html', response="At least one topic is required.", error=True)
        
        if author_id in supervisors or author_id in cosupervisors:
            return render_template('result.html', response="Author cannot be a supervisor or cosupervisor.", error=True)
       
        """
        # Author tablosunda ilgili kişileri doğrula
        all_persons = set([author_id] + supervisors + cosupervisors)
        print(all_persons)
        cursor.execute("SELECT AuthorID FROM Author WHERE AuthorID IN ({})".format(','.join('?' * len(all_persons))), list(all_persons))
        valid_persons = {row[0] for row in cursor.fetchall()}
        if len(all_persons) > len(valid_persons):
            return render_template('result.html', response="Some persons (author, supervisors,cosupervisors) are not found in the Author table.", error=True)
        """
        # Topics tablosunda ilgili konuları doğrula
        cursor.execute("SELECT SubjectTopicID FROM SubjectTopic WHERE SubjectTopicID IN ({})".format(','.join('?' * len(topics))), topics)

        valid_topics = {row[0] for row in cursor.fetchall()}
        if len(topics) > len(valid_topics):
            return render_template('result.html', response="Some topics are not found in the SubjectTopic table.", error=True)

        # Thesis tablosuna veri ekle
        cursor.execute('''
            INSERT INTO Thesis (Title, Abstract, AuthorID, Year, ThesisType, UniversityID, InstituteID, PageCount, Language, SubmissionDate, SupervisorID, CoSupervisorID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, abstract, author_id, year, thesis_type, university_id, institute_id, num_pages, language, submission_date, supervisors[0] if supervisors else None, cosupervisors[0] if cosupervisors else None))
        cursor.commit()

        """ ÇALIŞMIYOR 
        # Eklenen tez ID'sini al
        cursor.execute("SELECT SCOPE_IDENTITY()")
        thesis_id = cursor.fetchone()[0]
        """
        cursor.execute("SELECT TOP 1 ThesisID FROM Thesis ORDER BY ThesisID DESC;")
        thesis_id = cursor.fetchall()[0][0]
        topic_id = topics[0]

        print((thesis_id, topic_id))
        # Topics ekle
        for topic_id in topics:
            cursor.execute("INSERT INTO ThesisSubjectTopic (ThesisID, SubjectTopicID) VALUES (?, ?)", (thesis_id, topic_id))
            cursor.commit()

        # Keywords ekle
        for keyword in keywords:
            cursor.execute("INSERT INTO Keyword (Keyword) OUTPUT INSERTED.KeywordID VALUES (?)", (keyword,))
            keyword_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO ThesisKeyword (ThesisID, KeywordID) VALUES (?, ?)", (thesis_id, keyword_id))

        # Değişiklikleri kaydet
        conn.commit()
        return render_template('result.html', response=f"Thesis added successfully. ThesisID: {thesis_id}")
    
    
    except pyodbc.Error as e:
        conn.rollback()
        return render_template('result.html', response=f"An error occurred: {str(e)}", error=True)
    finally:
        conn.close()

# search page
@app.route('/search', methods=['GET'])
def search():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        

        # Üniversite bilgilerini al
        cursor.execute("SELECT UniversityID, Name FROM University")
        university = cursor.fetchall()

        # Enstitü bilgilerini al (ve ilişkili üniversite bilgisiyle)
        cursor.execute("""
            SELECT Institute.InstituteID, Institute.Name, Institute.UniversityID, University.Name
            FROM Institute
            INNER JOIN University ON Institute.UniversityID = University.UniversityID
        """)
        institute = cursor.fetchall()

        # Kişi bilgilerini al (Yazarlar)
        cursor.execute("SELECT AuthorID, CONCAT(AuthorType, ' ' ,FirstName, ' ', LastName  ) AS Name FROM Author")

        author = cursor.fetchall()

        # Konu bilgilerini al
        cursor.execute("SELECT SubjectTopicID, TopicName FROM SubjectTopic")
        topics = cursor.fetchall()

        return render_template('search.html', university=university, institute=institute, author=author, subjecttopic=topics)

    except pyodbc.Error as e:
        return render_template('result.html', response=f"An error occurred: {str(e)}", error=True)
    finally:
        conn.close()
    

def generate_search_query(conditions):
    base_query = "SELECT ThesisID, Title, ThesisType, Year, Language, PageCount FROM Thesis WHERE 1=1"
    
    # Koşulları kontrol edip sorguya ekliyoruz
    if 'year' in conditions and conditions['year']:
        base_query += f" AND Year = {conditions['year']}"
    if 'author' in conditions and conditions['author']:
        base_query += f" AND AuthorID = {conditions['author']}"
    if 'university' in conditions and conditions['university']:
        base_query += f" AND UniversityID = {conditions['university']}"
    if 'institute' in conditions and conditions['institute']:
        base_query += f" AND InstituteID = {conditions['institute']}"
    if 'topics' in conditions and conditions['topics']:
        base_query += f" AND ThesisID IN (SELECT ThesisID FROM ThesisSubjectTopic WHERE SubjectTopicID = {conditions['topic']})"
    
    return base_query


@app.route('/search_thesis', methods=['POST'])
def search_thesis():
    conditions = request.form.to_dict()  # Formdan gelen verileri alıyoruz
    try:
        # generate_search_query fonksiyonuyla, gelen şartlara göre SQL sorgusu oluşturuluyor
        query = generate_search_query(conditions)
    except ValueError as e:
        return render_template('result.html', response=str(e), error=True)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query)  # SQL sorgusunu çalıştırıyoruz
        result = cursor.fetchall()  # Sorgu sonucunu alıyoruz

        # Kolon isimlerini alıyoruz
        column_names = [desc[0] for desc in cursor.description]
        
        # Sonuçları dictionary formatına çeviriyoruz
        result_dict = [dict(zip(column_names, row)) for row in result]

        return render_template('search_result.html', response=result_dict)
    
    except pyodbc.Error as e:
        return render_template('result.html', response=f"An error occurred: {str(e)}", error=True)
    
    finally:
        conn.close()  # Veritabanı bağlantısını kapatıyoruz


@app.route('/get_thesis/<int:id>', methods=['GET'])
def get_thesis(id):
    try:
        # Thesis details query
        conn = get_db_connection()
        cursor = conn.cursor()
        """
        cursor.execute('''SELECT 
                Thesis.ThesisID,
                Author.FirstName + ' ' + Author.LastName AS author_name,
                Supervisor.FirstName + ' ' + Supervisor.LastName AS supervisor_name,
                CoSupervisor.FirstName + ' ' + CoSupervisor.LastName AS cosupervisor_name,
                Thesis.Title,
                Thesis.Abstract,
                University.Name AS university_name,
                Institute.Name AS institute_name,
                Thesis.SubmissionDate,
                Thesis.PageCount,
                Thesis.Language,
                Thesis.Year,
                Thesis.ThesisType
            FROM Thesis
            LEFT JOIN Author AS Author ON Thesis.AuthorID = Author.AuthorID
            LEFT JOIN Author AS Supervisor ON Thesis.SupervisorID = SupervisorInfo.SupervisorID
            LEFT JOIN Author AS CoSupervisor ON Thesis.CoSupervisorID = SupervisorInfo.SupervisorID
            LEFT JOIN University ON Thesis.UniversityID = University.UniversityID
            LEFT JOIN Institute ON Thesis.InstituteID = Institute.InstituteID
            WHERE Thesis.ThesisID = ?;''', (id,))
        """
        
        cursor.execute("""
            SELECT 
                Thesis.ThesisID,
                Thesis.Title,
                Thesis.Abstract,
                Thesis.Year,
                Thesis.PageCount,
                Thesis.Language,
                Thesis.SubmissionDate,
                Thesis.ThesisType,
                
                -- Author Details
                Author.AuthorType + ' ' + Author.FirstName + ' ' + Author.LastName as AuthorName,

                -- Supervisor Details
                SupervisorInfo.Title + ' ' + SupervisorInfo.FirstName + ' ' + SupervisorInfo.LastName AS SupervisorName,

                CoSupervisor.Title + ' ' + CoSupervisor.FirstName + ' ' + CoSupervisor.LastName AS CoSupervisorName,

                -- University Details
                University.Name AS UniversityName,
                
                -- Institute Details
                Institute.Name AS InstituteName,
                
                -- Keywords (Comma Separated)
                STRING_AGG(Keyword.Keyword, ', ') AS ThesisKeywords,
                
                -- Subject Topics (Comma Separated)
                STRING_AGG(SubjectTopic.TopicName, ', ') AS ThesisTopics

            FROM Thesis
            -- Join Author Table
            LEFT JOIN Author ON Thesis.AuthorID = Author.AuthorID

            -- Join Supervisor Table
            LEFT JOIN SupervisorInfo ON Thesis.SupervisorID = SupervisorInfo.SupervisorID
            LEFT JOIN SupervisorInfo AS CoSupervisor ON Thesis.CoSupervisorID = CoSupervisor.SupervisorID

            -- Join University Table
            LEFT JOIN University ON Thesis.UniversityID = University.UniversityID

            -- Join Institute Table
            LEFT JOIN Institute ON Thesis.InstituteID = Institute.InstituteID

            -- Join Thesis-Keyword Relation and Keyword Table
            LEFT JOIN ThesisKeyword ON Thesis.ThesisID = ThesisKeyword.ThesisID
            LEFT JOIN Keyword ON ThesisKeyword.KeywordID = Keyword.KeywordID

            -- Join Thesis-SubjectTopic Relation and SubjectTopic Table
            LEFT JOIN ThesisSubjectTopic ON Thesis.ThesisID = ThesisSubjectTopic.ThesisID
            LEFT JOIN SubjectTopic ON ThesisSubjectTopic.SubjectTopicID = SubjectTopic.SubjectTopicID
                       
            WHERE Thesis.ThesisID = ?

            -- Group by Thesis Attributes and Related Single-Value Columns
            GROUP BY 
                Thesis.ThesisID,
                Thesis.Title,
                Thesis.Abstract,
                Thesis.Year,
                Thesis.PageCount,
                Thesis.Language,
                Thesis.SubmissionDate,
                Thesis.ThesisType,
                Author.FirstName,
                Author.LastName,
                Author.AuthorType,
                SupervisorInfo.FirstName,
                SupervisorInfo.LastName,
                SupervisorInfo.Title,
                CoSupervisor.FirstName,
                CoSupervisor.LastName,
                CoSupervisor.Title,
                University.Name,
                University.City,
                University.Country,
                University.EstablishedYear,
                Institute.Name,
                Institute.InstituteType,
                Institute.EstablishedYear;

                       """, (id,))

        
        thesis_details = cursor.fetchall()

        if not thesis_details:
            return render_template('result.html', response="Thesis not found.", error=True)

        thesis_details_dict = dict(zip([desc[0] for desc in cursor.description], thesis_details[0]))

        # Keywords query
        cursor.execute('''SELECT 
                Keyword.Keyword
            FROM ThesisKeyword
            LEFT JOIN Keyword ON ThesisKeyword.KeywordID = Keyword.KeywordID
            WHERE ThesisKeyword.ThesisID = ?;''', (id,))
        keywords = [item[0] for item in cursor.fetchall()]

        # Topics query
        cursor.execute('''SELECT 
                SubjectTopic.TopicName
            FROM ThesisSubjectTopic
            LEFT JOIN SubjectTopic ON ThesisSubjectTopic.SubjectTopicID = SubjectTopic.SubjectTopicID
            WHERE ThesisSubjectTopic.ThesisID = ?;''', (id,))
        topics = [item[0] for item in cursor.fetchall()]

        result = {'thesis': thesis_details_dict, 'keywords': keywords, 'topics': topics}
        print(result)
        return render_template('thesis.html', result=result)

    except Exception as e:
        return render_template('result.html', response=str(e), error=True)
    finally:
        conn.close()

@app.route('/edit')
def edit():
    conn = get_db_connection()
    cursor = conn.cursor()
    # get thesis
    cursor.execute("SELECT ThesisID, Title, ThesisType, Year, Language, PageCount FROM Thesis")
    thesis = cursor.fetchall()

    # get university names 
    cursor.execute("SELECT UniversityID, Name, City, Country, EstablishedYear FROM University")
    universities = cursor.fetchall()
    # query that gets institute names and its university name
    cursor.execute("SELECT Institute.InstituteID, Institute.Name, Institute.UniversityID, University.Name, Institute.InstituteType, Institute.EstablishedYear FROM Institute INNER JOIN University ON Institute.UniversityID = University.UniversityID")
    institutes = cursor.fetchall()
    # get person names
    cursor.execute("SELECT AuthorID, AuthorType, FirstName, LastName FROM Author")
    authors = cursor.fetchall()
    # get topic names
    cursor.execute("SELECT SubjectTopicID ,TopicName FROM SubjectTopic")    
    topics = cursor.fetchall()
    # get keywords
    cursor.execute("SELECT KeywordID, keyword FROM Keyword")
    keywords = cursor.fetchall()

    return render_template('edit.html', thesis=thesis, universities=universities, institutes=institutes, authors=authors, topics=topics, keywords=keywords)


@app.route('/edit_author/<int:id>', methods=['POST'])
def edit_author(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    title = request.form.get('title')
    firstname = request.form.get('firstname')
    surname = request.form.get('surname')
    try:
        cursor.execute("UPDATE Author SET AuthorType = ?, FirstName = ?, LastName=? WHERE AuthorID = ?", (title, firstname, surname, id))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Author updated successfully")

@app.route('/delete_author/<int:id>', methods=['POST'])
def delete_author(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM Thesis WHERE AuthorID = ?", (id,))
        cursor.execute("DELETE FROM Author WHERE AuthorID = ?", (id,))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Author deleted successfully")

@app.route('/edit_topic/<int:id>', methods=['POST'])
def edit_topic(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    name = request.form.get('name')
    try:
        cursor.execute("UPDATE SubjectTopic SET TopicName = ? WHERE SubjectTopicID = ?", (name, id))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Topic updated successfully")

@app.route('/delete_topic/<int:id>', methods=['POST'])
def delete_topic(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM SubjectTopic WHERE SubjectTopicID = ?", (id,))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Topic deleted successfully")

@app.route('/edit_university/<int:id>', methods=['POST'])
def edit_university(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    name = request.form.get('name')
    try:
        cursor.execute("UPDATE University SET Name = ? WHERE UniversityID = ?", (name, id))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="University updated successfully")

@app.route('/delete_university/<int:id>', methods=['POST'])
def delete_university(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM University WHERE UniversityID = ?", (id,))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="University deleted successfully")

@app.route('/edit_institute/<int:id>', methods=['POST'])
def edit_institute(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    name = request.form.get('name')
    type = request.form.get('type')
    year = request.form.get('year')
    try:
        cursor.execute("UPDATE Institute SET Name = ?, InstituteType = ?, EstablishedYear = ? WHERE InstituteID = ?", (name, type, year, id))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Institute updated successfully")

@app.route('/delete_institute/<int:id>', methods=['POST'])
def delete_institute(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Institute WHERE InstituteID = ?", (id,))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Institute deleted successfully")

@app.route('/edit_thesis/<int:id>', methods=['POST'])
def edit_thesis(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    title = request.form.get('title')
    type = request.form.get('type')
    year = request.form.get('year')
    language = request.form.get('language')
    pagecount = request.form.get('pagecount')

    try:
        cursor.execute("UPDATE Thesis SET Title = ?, ThesisType = ?, Year = ?, Language = ?, PageCount = ? WHERE ThesisID = ?", (title, type, year, language, pagecount, id))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Thesis updated successfully")

@app.route('/delete_thesis/<int:id>', methods=['POST'])
def delete_thesis(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM ThesisKeyword WHERE ThesisID = ?", (id,))
        cursor.commit()
        cursor.execute("DELETE FROM ThesisSubjectTopic WHERE ThesisID = ?", (id,))
        cursor.commit()
        cursor.execute("DELETE FROM Thesis WHERE ThesisID = ?", (id,))
        cursor.commit()
    except pyodbc.Error as e:
        return render_template('result.html', response=(e), error=True)
    return render_template('result.html', response="Thesis deleted successfully")

# Flask uygulamasını çalıştırma
if __name__ == '__main__':
    app.run(debug=True)
