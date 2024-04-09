import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QProgressBar, QLineEdit, QRadioButton, QTextEdit, QTableWidget, QTableWidgetItem, QButtonGroup
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QDateTime
import pyqtgraph as pg
import time
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QColor, QImage
import os
import pymysql

_1x = 0.1 #DELAY
_2x = 0.01 #DELAY

judgement_data = {
    "blending": [
        ("MOVE_X+", '1'),
        ("MOVE_X+", '2'),
        ("MOVE_Y+", '1'),
        ("MOVE_Y+", '2'),
        ("MOVE_Y+", '3'),
        ("MOVE_Y+", '4'),
        ("MOVE_X+", '3'),
        ("MOVE_X+", '4'),
        ("MOVE_Y-", '3'),
        ("MOVE_Y-", '2'),
        ("MOVE_Y-", '1'),
        ("MOVE_Y-", '0'),
        ("MOVE_X+", '5'),
        ("MOVE_X+", '6'),
        ("HOME_X",	'5'),
        ("HOME_X",	'4'),
        ("HOME_X",	'3'),
        ("HOME_X",	'2'),
        ("HOME_X",	'1'),
        ("HOME_X",	'0')
    ]
}


class ClickThread(QThread):
    update_signal = pyqtSignal(object)

    def __init__(self, clicks, delay, parent=None):
        super().__init__(parent)
        self.clicks = clicks
        self.delay = delay        

    def run(self):
        for click in self.clicks:
            self.update_signal.emit(click)            
            time.sleep(self.delay)  

class SQLExecutor:
    def execute_sql_file(self, filename, connection):
        # SQL 파일 열기
        with open(filename, 'r') as file:
            sql = file.read()

        # SQL 문 실행
        with connection.cursor() as cursor:
            #sql = "USE judge_db;"
            cursor.execute(sql)
            connection.commit()       
                
    def __init__(self):
        super().__init__()
        
        # MySQL 연결 설정
        self.connection = pymysql.connect(
            host='localhost',
            user='root',
            password='0000',
            database='judge_db',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        # 현재 스크립트 파일의 디렉토리를 가져옴
        script_dir = os.path.dirname(os.path.realpath(__file__))
        
        # 실행할 SQL 파일 경로
        sql_file = os.path.join(script_dir, 'sql/데이터베이스연결.sql')

        # SQL 파일 실행
        self.execute_sql_file(sql_file, self.connection)
        
        
        # 실행할 SQL 파일 경로
        sql_file = os.path.join(script_dir, 'sql/blending검사.sql')

        # SQL 파일 실행
        self.execute_sql_file(sql_file, self.connection)
        

        # 연결 종료
        self.connection.close()

class XAxisController(QMainWindow):  
    def __init__(self):
        super().__init__()
    
        # 현재 스크립트 파일의 디렉토리를 가져옴
        script_dir = os.path.dirname(os.path.realpath(__file__))
    
        # 배경색을 변경하기 위해 QPalette를 생성합니다.
        palette = self.palette()
        # 고급스러운 주황색 계열 색상으로 설정합니다.
        palette.setColor(QPalette.Window, QColor(255, 255, 255))  # RGB 값을 지정하여 원하는 배경색을 설정합니다.
        self.setPalette(palette)
        
        # 아이콘 파일의 경로 생성
        icon_path = os.path.join(script_dir, 'icon.jpeg')

        # 타이틀바 아이콘 변경
        self.setWindowIcon(QIcon(icon_path))
        
        self.setWindowTitle("Motion Pattern Analysis")
        self.setGeometry(100, 100, 300, 700)

        self.delay = 0.1
        self.reproduce_count = 0  # 재현 횟수를 저장할 변수 추가
        self.update_count = 0

        self.auto_test_end_flag = False
        self.x_position = 0
        self.y_position = 0
        self.move_speed = 1
        self.max_distance = 10
        self.home_Sensor_x = False
        self.home_Sensor_y = False
        self.testing = False
        self.home_x_timer = None
        self.home_y_timer = None
        self.judge = ""
        self.classification = ""#"Blending"                

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.label_reproduce_count = QLabel(f"재현 횟수: {self.reproduce_count}", self)  # 재현 횟수를 표시할 QLabel 위젯 추가
        self.layout.addWidget(self.label_reproduce_count)  # 레이아웃에 위젯 추가
        self.label_reproduce_count.setVisible(False)

        self.label_x = QLabel(f"X 축 위치: {self.x_position}", self)
        self.layout.addWidget(self.label_x)
        self.label_x.setVisible(False)
        
        self.label_y = QLabel(f"Y 축 위치: {self.y_position}", self)
        self.layout.addWidget(self.label_y)
        self.label_y.setVisible(False)
        
        self.label_judge = QLabel(f"판정 : {self.judge}", self)
        self.layout.addWidget(self.label_judge)
        self.label_judge.setVisible(False)
        
        self.label_classification = QLabel(f"분류 : {self.classification}", self)
        self.layout.addWidget(self.label_classification)
        self.label_classification.setVisible(False)
        
        # 텍스트를 표시할 QTextEdit 위젯 생성
        self.judge_textEdit = QTextEdit(self)
        # 사용자 입력 비활성화
        self.judge_textEdit.setReadOnly(True)
        # 텍스트 설정 (선택사항)
        self.judge_textEdit.setText("")     
        self.judge_textEdit.setFixedSize(310, 100)
        self.layout.addWidget(self.judge_textEdit)
        self.judge_textEdit.setVisible(False)
        
        # QTableWidget 생성
        self.judge_tableWidget = QTableWidget(self)
        self.judge_tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)  # 사용자 입력 비활성화
        #self.judge_tableWidget.setFixedSize(310, 100)
        self.judge_tableWidget.setFixedHeight(100)

        # 테이블에 열 추가
        self.judge_tableWidget.setColumnCount(3)
        
        # 헤더 텍스트 설정
        self.judge_tableWidget.setHorizontalHeaderLabels(["판정", "분류", "시간"])

        # 헤더 객체에 접근하여 왼쪽 정렬로 설정
        header = self.judge_tableWidget.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft)

        # 위젯 레이아웃에 QTableWidget 추가
        self.layout.addWidget(self.judge_tableWidget)
    

        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setXRange(0, self.max_distance)
        self.graphWidget.setYRange(0, self.max_distance)
        self.layout.addWidget(self.graphWidget)        
        self.graphWidget.setBackground('w')  # 흰색 배경으로 설정
        #self.graphWidget.getAxis('left').setLabel('Y Axis Label', color='b')
        #self.graphWidget.getAxis('bottom').setLabel('X Axis Label', color='b')

        self.graph_data = [(self.x_position,self.y_position)]

        # 재현 횟수를 표현하는 프로그레스 바 추가
        self.reproduce_progress_bar = QProgressBar(self)
        self.reproduce_progress_bar.setRange(0, 100)  # 프로그레스 바 범위 설정 (0~100)
        self.reproduce_progress_bar.setFormat("재현 : %p"+'%')  # 텍스트 형식을 설정합니다.
        self.layout.addWidget(self.reproduce_progress_bar)  # 레이아웃에 위젯 추가    

        self.x_progress_bar = QProgressBar(self)
        self.x_progress_bar.setRange(0, self.max_distance)
        self.x_progress_bar.setFormat("X축 : %p"+'%')  # 텍스트 형식을 설정합니다.        
        self.layout.addWidget(self.x_progress_bar)
        
        self.y_progress_bar = QProgressBar(self)
        self.y_progress_bar.setRange(0, self.max_distance)
        self.y_progress_bar.setFormat("Y축 : %p"+'%')  # 텍스트 형식을 설정합니다.     
        self.layout.addWidget(self.y_progress_bar)    

        self.move_x_plus_button = QPushButton("MOVE X +", self)
        self.move_x_plus_button.clicked.connect(self.move_x_axis_plus)
        #self.move_x_plus_button.setFixedSize(120, 50)     
        self.move_x_plus_button.setFixedHeight(50)

        self.move_x_plus_button.setStyleSheet('''
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
            }
            QPushButton:disabled {
                background-color: #fff0da;
                color: #888888;
                border: none;
            }
            
        ''')
        #self.move_x_plus_button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: white;}')
        #self.move_x_plus_button.setFocusPolicy(Qt.NoFocus)  # Tab으로 포커스를 받지 않도록 설정
        #self.move_x_plus_button.setStyleSheet("border: none;")  # 테두리 스타일을 없애기
        
        # QPushButton의 그라데이션 배경 설정 예시
        #gradient = "background: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.5, fx: 0.5, fy: 0.5, stop: 0.5 #FFFFFF, stop: 1.0 #000000);"
        #self.move_x_plus_button.setStyleSheet(gradient)            
        
        self.move_y_plus_button = QPushButton("MOVE Y +", self)
        self.move_y_plus_button.clicked.connect(self.move_y_axis_plus)
        #self.move_y_plus_button.setFixedSize(120, 50)
        self.move_y_plus_button.setFixedHeight(50)
        
        self.move_y_plus_button.setStyleSheet('''
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
            }
            QPushButton:disabled {
                background-color: #fff0da;
                color: #888888;
                border: none;
            }
            
        ''')
        
        self.move_x_minus_button = QPushButton("MOVE X -", self)
        self.move_x_minus_button.clicked.connect(self.move_x_axis_minus)
        #self.move_x_minus_button.setFixedSize(120, 50) 
        self.move_x_minus_button.setFixedHeight(50)            
        
        self.move_x_minus_button.setStyleSheet('''
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
            }
            QPushButton:disabled {
                background-color: #fff0da;
                color: #888888;
                border: none;
            }
            
        ''')          

        self.move_y_minus_button = QPushButton("MOVE Y -", self)
        self.move_y_minus_button.clicked.connect(self.move_y_axis_minus)
        #self.move_y_minus_button.setFixedSize(120, 50)
        self.move_y_minus_button.setFixedHeight(50)                
        
        self.move_y_minus_button.setStyleSheet('''
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
            }
            QPushButton:disabled {
                background-color: #fff0da;
                color: #888888;
                border: none;
            }
            
        ''')         

        self.home_x_button = QPushButton("HOME X", self)
        self.home_x_button.clicked.connect(self.start_home_x_timer)       
        #self.home_x_button.setFixedSize(120, 50)        
        self.home_x_button.setFixedHeight(50)                
        
        self.home_x_button.setStyleSheet('''
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
            }
            QPushButton:disabled {
                background-color: #fff0da;
                color: #888888;
                border: none;
            }
            
        ''') 
        
        self.home_y_button = QPushButton("HOME Y", self)
        self.home_y_button.clicked.connect(self.start_home_y_timer)        
        #self.home_y_button.setFixedSize(120, 50)
        self.home_y_button.setFixedHeight(50)                
        
        self.home_y_button.setStyleSheet('''
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
            }
            QPushButton:disabled {
                background-color: #fff0da;
                color: #888888;
                border: none;
            }
            
        ''')                 

        self.test_auto_button = QPushButton("재현", self)
        self.test_auto_button.clicked.connect(self.auto_test)        
        self.test_auto_button.setFixedSize(120, 50)
        #self.test_auto_button.setFixedHeight(50)                
        #self.test_auto_button.setFixedWidth(120)
        
        self.test_auto_button.setStyleSheet('''
            QPushButton {
                background-color: #00498C;
                color: white;
                border: none;
            }
            QPushButton:disabled {
                background-color: #b6bed8;
                color: #888888;
                border: none;
            }
            
        ''')           
        
        self.repeat_count_edit = QLineEdit(self)
        self.repeat_count_edit.setPlaceholderText("반복 횟수 입력")
        #self.repeat_count_edit.setFixedSize(120, 50)
        self.repeat_count_edit.setAlignment(Qt.AlignCenter)
        self.repeat_count_edit.setFixedHeight(50)   
        
        self.delay_radio_1x = QRadioButton("1X", self)
        self.delay_radio_1x.setChecked(True)
        
        self.delay_radio_2x = QRadioButton("2X", self)
        
        delay_radio_layout = QVBoxLayout()
        #delay_radio_layout.addWidget(self.delay_radio_1x, alignment=Qt.AlignCenter)
        #delay_radio_layout.addWidget(self.delay_radio_2x, alignment=Qt.AlignCenter)
        delay_radio_layout.addWidget(self.delay_radio_1x, alignment=Qt.AlignLeft)
        delay_radio_layout.addWidget(self.delay_radio_2x, alignment=Qt.AlignLeft)        
        
        move_buttons_plus_layout = QHBoxLayout()
        move_buttons_plus_layout.addWidget(self.move_x_plus_button)
        move_buttons_plus_layout.addWidget(self.move_y_plus_button)

        move_buttons_minus_layout = QHBoxLayout()
        move_buttons_minus_layout.addWidget(self.move_x_minus_button)
        move_buttons_minus_layout.addWidget(self.move_y_minus_button)        

        home_buttons_layout = QHBoxLayout()
        home_buttons_layout.addWidget(self.home_x_button)
        home_buttons_layout.addWidget(self.home_y_button)
        
        test_auto_buttons_layout = QHBoxLayout()
        test_auto_buttons_layout.addLayout(delay_radio_layout)
        test_auto_buttons_layout.addWidget(self.test_auto_button)
        test_auto_buttons_layout.addWidget(self.repeat_count_edit)
        
        
        self.layout.addLayout(move_buttons_plus_layout)
        self.layout.addLayout(move_buttons_minus_layout)   
        self.layout.addLayout(home_buttons_layout)        
        self.layout.addLayout(test_auto_buttons_layout)        
        

        self.log_file = open("button_log.txt", "a")
        
        self.update_graph()     
        
    def move_x_axis_plus(self):
        if self.x_position == 0:
            self.home_Sensor_x = True
        else:
            self.home_Sensor_x = False       
                         
        if self.x_position < self.max_distance:
            distance_to_move = min(self.move_speed, self.max_distance - self.x_position)
            self.x_position += distance_to_move
            self.label_x.setText(f"X 축 위치: {self.x_position}")
            log_message = f"MOVE_X+\t{self.x_position}\n"
            if not self.testing:
                self.write_to_log(log_message)

            self.graph_data.append((self.x_position, self.y_position))
            self.update_graph()
            self.x_progress_bar.setValue(self.x_position)                        
            
        if self.x_position != 0:
            self.home_Sensor_x = False
        else:
            self.home_Sensor_x = True
        
    def move_y_axis_plus(self):
        if self.y_position == 0:
            self.home_Sensor_y = True
        else:
            self.home_Sensor_y = False    
                
        if self.y_position < self.max_distance:
            distance_to_move = min(self.move_speed, self.max_distance - self.y_position)
            self.y_position += distance_to_move
            self.label_y.setText(f"Y 축 위치: {self.y_position}")
            log_message = f"MOVE_Y+\t{self.y_position}\n"
            if not self.testing:
                self.write_to_log(log_message)

            self.graph_data.append((self.x_position, self.y_position))
            self.update_graph()
            self.y_progress_bar.setValue(self.y_position)
            
        if self.y_position != 0:
            self.home_Sensor_y = False
        else:
            self.home_Sensor_y = True
                
                
    
    def move_x_axis_minus(self):  # minus 방향 버튼 클릭 시 실행되는 함수
        if self.x_position == 0:
            self.home_Sensor_x = True
        else:
            self.home_Sensor_x = False
        
        if self.x_position > 0:  # 위치가 0보다 큰 경우에만 감소
            distance_to_move = min(self.move_speed, self.x_position)
            self.x_position -= distance_to_move
            self.label_x.setText(f"X 축 위치: {self.x_position}")
            log_message = f"MOVE_X-\t{self.x_position}\n"  # minus 방향 버튼이므로 MOVE_X_MINUS로 로그 작성
            if not self.testing:
                self.write_to_log(log_message)

            self.graph_data.append((self.x_position, self.y_position))
            self.update_graph()
            self.x_progress_bar.setValue(self.x_position)
            
        if self.x_position == 0:
            self.home_Sensor_x = True
        else:
            self.home_Sensor_x = False

    def move_y_axis_minus(self):  # minus 방향 버튼 클릭 시 실행되는 함수
        if self.y_position == 0:
            self.home_Sensor_y = True
        else:
            self.home_Sensor_y = False
                    
        if self.y_position > 0:  # 위치가 0보다 큰 경우에만 감소
            distance_to_move = min(self.move_speed, self.y_position)
            self.y_position -= distance_to_move
            self.label_y.setText(f"Y 축 위치: {self.y_position}")
            log_message = f"MOVE_Y-\t{self.y_position}\n"  # minus 방향 버튼이므로 MOVE_Y_MINUS로 로그 작성
            if not self.testing:
                self.write_to_log(log_message)

            self.graph_data.append((self.x_position, self.y_position))
            self.update_graph()
            self.y_progress_bar.setValue(self.y_position)
            
        if self.y_position == 0:
            self.home_Sensor_y = True
        else:
            self.home_Sensor_y = False                    
                
    def start_home_x_timer(self):
        if self.x_position > 0:
            if not self.home_x_timer:
                self.home_x_timer = QTimer(self)
                self.home_x_timer.timeout.connect(self.home_x_axis)                
                self.home_x_timer.start(100)  
    
    def start_home_y_timer(self):
        if self.y_position > 0:
           if not self.home_y_timer:
                self.home_y_timer = QTimer(self)
                self.home_y_timer.timeout.connect(self.home_y_axis)                
                self.home_y_timer.start(100) 
                                    

    def home_x_axis(self):
        if self.x_position == 0:
            self.home_Sensor_x = True            
        else:
            self.home_Sensor_x = False
            
        log_message = f"HOME X\t{self.x_position}\n"      
            
        if self.x_position > 0:                                    
            distance_to_move = min(self.x_position, self.move_speed)
            self.x_position -= distance_to_move
            self.label_x.setText(f"X 축 위치: {self.x_position}")
            log_message = f"HOME_X\t{self.x_position}\n"
            if not self.testing:
                self.write_to_log(log_message)

            self.graph_data.append((self.x_position, self.y_position))
            self.update_graph()
            self.x_progress_bar.setValue(self.x_position)
            
            if self.x_position == 0:                                    
                self.init_x_graph_progress()
            
        else:
            if self.home_x_timer:
                self.home_x_timer.stop()
                self.home_x_timer = None
                self.init_x_graph_progress()
            
    def home_y_axis(self):
        if self.y_position == 0:
            self.home_Sensor_y = True
        else:
            self.home_Sensor_y = False
            
        log_message = f"HOME_Y\t{self.y_position}\n"
                
        if self.y_position > 0:                                    
            distance_to_move = min(self.y_position, self.move_speed)
            self.y_position -= distance_to_move
            self.label_y.setText(f"Y 축 위치: {self.y_position}")
            log_message = f"HOME_Y\t{self.y_position}\n"
            if not self.testing:
                self.write_to_log(log_message)

            self.graph_data.append((self.x_position, self.y_position))
            self.update_graph()
            self.y_progress_bar.setValue(self.y_position)
            
            if self.y_position == 0:                                    
                self.init_y_graph_progress()
            
        else:
            if self.home_y_timer:
                self.home_y_timer.stop()
                self.home_y_timer = None
                self.init_y_graph_progress()            

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '종료', "프로그램을 종료하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.log_file.close()
            event.accept()
        else:
            event.ignore()
            
    
    def auto_test(self):
        # SQLExecutor 클래스의 인스턴스 생성
        self.sql_executor = SQLExecutor()
        
        if self.repeat_count_edit.text() == '':
            QMessageBox.warning(self, "경고", "반복 횟수를 입력하세요.", QMessageBox.Ok)
            return
        
        repeat_count = int(self.repeat_count_edit.text())  
        if repeat_count <= 0:
            QMessageBox.warning(self, "경고", "반복 횟수는 양의 정수이어야 합니다.", QMessageBox.Ok)
            return
        
        else:                        
            if self.x_position == 0:
                self.home_Sensor_x = True
            else:
                self.home_Sensor_x = False
                
            if self.y_position == 0:
                self.home_Sensor_y = True
            else:
                self.home_Sensor_y = False            
            
            with open("button_log.txt", "r") as log_file:
                pass
            
            if True == self.home_Sensor_x and True == self.home_Sensor_y:
                self.testing = True
                self.setButtonDisabled()

                button_clicks = self.read_button_log("button_log.txt")

                self.set_delay()

                self.click_thread = ClickThread(button_clicks * repeat_count, self.delay)
                self.click_thread.update_signal.connect(self.process_button_click)
                self.click_thread.start()
 
                
                QTimer.singleShot((int(self.delay * 1000) * len(button_clicks)*repeat_count)+1000, self.set_testing_to_false)
                
                
            else:
                if False == self.home_Sensor_x: 
                    QMessageBox.warning(self, "경고", "X축 홈 위치가 아닙니다.", QMessageBox.Ok)
                    
                if False == self.home_Sensor_y:                
                    QMessageBox.warning(self, "경고", "Y축 홈 위치가 아닙니다.", QMessageBox.Ok)
                    
    def set_delay(self):
        if self.delay_radio_1x.isChecked():
            self.delay = _1x
        elif self.delay_radio_2x.isChecked():
            self.delay = _2x
        else:
            print("delay radio button error")        
    
    def set_testing_to_false(self):
        # 스레드가 정지되었는지 확인
        if not self.click_thread.isRunning():
            self.testing = False
            self.setButtonEnabled()
            #print("set_testing_to_false")
            self.pattern_judge()
            self.init_reproduce_info()
            self.init_judge()
            self.init_classification()
                        
        else:
            # 스레드가 아직 실행 중인 경우, 재귀적으로 다시 호출하여 잠시 후에 다시 확인합니다.
            QTimer.singleShot(1000, self.set_testing_to_false)
            
    def init_reproduce_info(self):
        self.reproduce_count = 0
        self.update_count = 0
        self.label_reproduce_count.setText(f"재현 횟수: {self.update_count}")
        self.reproduce_progress_bar.setValue(0)
        self.repeat_count_edit.setText("")                   
        
    def init_judge(self):
        self.label_judge.setText("판정 : ")
        
    def init_classification(self):
        self.label_classification.setText("분류 : ")
    
    def pattern_judge(self):     
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")   
        button_clicks = self.read_button_log("button_log.txt") 
        patterns = judgement_data["blending"]               

        if all(tuple(click) in patterns for click in button_clicks):            
            self.classification = "blending"
            self.judge = "Pass"
        else:            
            self.classification = "Miscellaneous"
            self.judge = "Fail" 

        print(self.judge)
        print(self.classification)
        #self.label_classification.setText("분류: " + self.classification)
        #self.label_judge.setText("판정: " + self.judge)

        # QTableWidget에 행 추가
        row_position = self.judge_tableWidget.rowCount()
        self.judge_tableWidget.insertRow(row_position)

        # 현재 시간을 오른쪽으로 정렬하여 표에 추가
        current_time_aligned = current_time.rjust(1, ' ')
        # current_time을 오른쪽으로 정렬하여 QTextEdit 위젯에 추가
        #current_time_aligned = current_time.rjust(30, ' ')  # 적절한 값으로 조정
        #self.judge_textEdit.append("판정: " + self.judge + "\t" +current_time_aligned)
        #self.judge_textEdit.append("분류: " + self.classification + current_time_aligned)

        # 테이블 셀에 텍스트 추가
        self.judge_tableWidget.setColumnWidth(0, 40)  # 첫 번째 열의 폭 조정
        self.judge_tableWidget.setColumnWidth(1, 80)  # 두 번째 열의 폭 조정
        self.judge_tableWidget.setColumnWidth(2, 150)  # 세 번째 열의 폭 조정
        self.judge_tableWidget.setItem(row_position, 0, QTableWidgetItem(self.judge))#판정
        self.judge_tableWidget.setItem(row_position, 1, QTableWidgetItem(self.classification))#분류
        self.judge_tableWidget.setItem(row_position, 2, QTableWidgetItem(current_time_aligned))#시간                                     

    def setButtonDisabled(self):
        self.move_x_plus_button.setEnabled(False)
        self.move_y_plus_button.setEnabled(False)
        self.move_x_minus_button.setEnabled(False)
        self.move_y_minus_button.setEnabled(False)
        self.home_x_button.setEnabled(False)        
        self.home_y_button.setEnabled(False)
        self.test_auto_button.setEnabled(False)
        self.repeat_count_edit.setDisabled(True)
    
    def setButtonEnabled(self):
        self.move_x_plus_button.setEnabled(True)
        self.move_y_plus_button.setEnabled(True)
        self.move_x_minus_button.setEnabled(True)
        self.move_y_minus_button.setEnabled(True)        
        self.home_x_button.setEnabled(True)        
        self.home_y_button.setEnabled(True)
        self.test_auto_button.setEnabled(True)
        self.repeat_count_edit.setEnabled(True)    
        

    def process_button_click(self, click):
        if self.testing == True:
            self.setButtonDisabled()            
        else:
            self.setButtonEnabled()                                                    
            
        # 클릭을 처리하는 동안 실행된 횟수를 카운트                                                                        
        self.reproduce_count += 1                  
                
        if len(click) == 2:
            button, position = click                                  
            
            if button == "MOVE_X+":
                self.move_x_axis_plus()
            elif button == "MOVE_X-":
                self.move_x_axis_minus()                
            elif button == "MOVE_Y+":
                self.move_y_axis_plus()
            elif button == "MOVE_Y-":
                self.move_y_axis_minus()  
            elif button == "HOME_X":
                self.home_x_axis() 
            elif button == "HOME_Y":
                self.home_y_axis()    
            else:
                pass
        
        else:
            print(f"잘못된 버튼 정보: {click}")                        
        
        if True == self.home_Sensor_x or True == self.home_Sensor_y:
            self.update_count = int(self.reproduce_count / len(judgement_data['blending']))
            self.label_reproduce_count.setText(f"재현 횟수: {self.update_count}")
            # 재현 횟수 계산 및 프로그레스 바 업데이트
            # 프로그레스 바 값 설정 (0~100 범위로 변환)
            #(현재 재현 횟수 / 전체 반복 횟수) * 100
            repeat_count = int(self.repeat_count_edit.text()) 
            self.reproduce_progress_bar.setValue(int((self.update_count/repeat_count)*100))          
  
                                                                      
    def write_to_log(self, message):
        if not self.testing:
            self.log_file.write(message)
            self.log_file.flush()                          

    def update_graph(self):
        plot_item = self.graphWidget.getPlotItem()
        plot_item.clear()
        x_values = [point[0] for point in self.graph_data]
        y_values = [point[1] for point in self.graph_data]
        #plot_item.plot(x_values, y_values, pen=pg.mkPen(color='b', width=2))
        plot_item.plot(x_values, y_values, pen=pg.mkPen(color='g', width=2))
        if x_values and y_values:
            #plot_item.plot([x_values[-1]], [y_values[-1]], pen=None, symbol='o', symbolSize=10, symbolBrush=('r'))       
            plot_item.plot([x_values[-1]], [y_values[-1]], pen=None, symbol='+', symbolSize=12, symbolBrush=('r'))       

    def read_button_log(self, file_path):
        print("read_button_log")
        button_clicks = []
        try:            
            with open(file_path, "r") as file:
                lines = file.readlines()
                for line in lines:
                    button_info = line.strip().split("\t")
                    button_clicks.append(button_info)
        except FileNotFoundError:
            print(f"파일 '{file_path}'를 찾을 수 없습니다.")
        return button_clicks

    def init_x_graph_progress(self):
        self.graph_data = [(self.x_position,self.y_position)]
        self.update_graph()
        self.x_progress_bar.setValue(0)
        self.label_x.setText("X 축 위치: 0")
        self.home_Sensor_x = True
        
    def init_y_graph_progress(self):
        self.graph_data = [(self.x_position,self.y_position)]
        self.update_graph()
        self.y_progress_bar.setValue(0)
        self.label_y.setText("Y 축 위치: 0")
        self.home_Sensor_y = True


def show_logo(app):
    #로고 팝업 시작
    # 이미지 경로 설정
    
    # 현재 스크립트 파일의 디렉토리를 가져옴
    script_dir = os.path.dirname(os.path.realpath(__file__))
        
    # 아이콘 파일의 경로 생성
    image_path = os.path.join(script_dir, 'logo.jpeg')  # 이미지 파일 경로를 적절히 지정해주세요
    
    # 이미지를 띄울 QLabel 생성
    label = QLabel()
    
    # 이미지 불러오기
    pixmap = QPixmap(image_path)
    
    # QLabel에 이미지 설정
    label.setPixmap(pixmap)
    
    # 이미지 크기 설정 (화면 8분의 1 크기)
    label.resize(pixmap.width(), pixmap.height())
    

    
    # QLabel을 화면 중앙에 표시
    screen = app.primaryScreen().geometry()
    x = int((screen.width() - label.width()) / 2)
    y = int((screen.height() - label.height()) / 2)
    label.move(x, y)
    
    # 창의 타이틀바와 메뉴를 숨김
    label.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint)
    
    # QLabel 표시
    label.show()
    
    # 2초 후에 QLabel 닫기
    time.sleep(2)
    QTimer.singleShot(100, label.close)
    
    # Qt 이벤트 루프 처리
    app.processEvents()
    #로고 팝업 끝


def main():
    app = QApplication(sys.argv)
    show_logo(app)
    window = XAxisController()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":    
    main()
