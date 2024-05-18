import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap
import os

def main():
    app = QApplication(sys.argv)

    # 현재 스크립트 파일의 디렉토리를 가져옴
    script_dir = os.path.dirname(os.path.realpath(__file__))
        
    print("script_dir : " + script_dir)    
    # 아이콘 파일의 경로 생성
    image_path = os.path.join(script_dir, 'logo.jpeg')  # 이미지 파일 경로를 적절히 지정해주세요

    # QLabel 위젯 생성
    label = QLabel()

    # 이미지 불러오기
    pixmap = QPixmap(image_path)

    # QLabel에 이미지 설정
    label.setPixmap(pixmap)

    # QLabel을 보여줌
    label.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
