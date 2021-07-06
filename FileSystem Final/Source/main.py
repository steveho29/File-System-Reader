from ui import *

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tree = TreeFileWidget()
    tree.show()
    sys.exit(app.exec_())
