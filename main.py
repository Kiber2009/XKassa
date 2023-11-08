import sys
import sqlite3
import json
from datetime import datetime
from os import getenv
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog, QTableWidgetItem, QMessageBox, QTableWidget
from ui.loginDialod import Ui_loginDialog
from ui.app import Ui_MainWindow
from ui.userDialog import Ui_userDialog
from ui.itemDialog import Ui_itemDialog
from ui.itemSelectDialog import Ui_itemSelectDialog

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def ttl(table: QTableWidget, another=None):
    """
    Table to list
    :param QTableWidget table:
    :param list[tuple] another:
    :return list:
    """
    if another is None:
        another = []
    s = [[].copy() for _ in range(table.rowCount())]
    for i in range(len(s)):
        for j in range(table.columnCount()):
            s[i].append(table.item(i, j).text())
        s[i] = tuple(s[i])
    s += another
    return s


class ItemSelectDialog(QDialog, Ui_itemSelectDialog):
    def __init__(self, sender):
        super().__init__()
        self.setupUi(self)
        self.sender_ = sender
        self.btnSearch.clicked.connect(self.search_)
        self.btnCancel.clicked.connect(self.cancel)
        self.btnSave.clicked.connect(self.save)
        self.search_()

    def search_(self):
        self.item.clear()
        res = (self.sender_.db.cursor().execute(f"SELECT name FROM items WHERE name like '%{self.search.text()}%'")
               .fetchall())
        for i in [ii[0] for ii in res]:
            self.item.addItem(i)

    def cancel(self):
        self.close()

    def save(self):
        if self.item.currentText() == '':
            self.status.setText('Не выбран товар')
            return None
        elif self.amount.value() == 0:
            self.status.setText('Не указано количество')
            return None
        self.sender_.temp = (self.item.currentText(), self.amount.value())
        self.close()


class ItemDialog(QDialog, Ui_itemDialog):
    def __init__(self, sender):
        super().__init__()
        self.id_ = None
        self.setupUi(self)
        self.sender_ = sender
        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.cancel)

    def get(self, id_, name, cost, type_):
        self.id_ = id_
        self.name.setText(name)
        self.cost.setValue(float(cost.replace(',', '.')))
        if int(type_):
            self.radioMass.setChecked(True)
            self.radioCount.setChecked(False)
        else:
            self.radioCount.setChecked(True)
            self.radioMass.setChecked(False)

    def cancel(self):
        self.close()

    def save(self):
        if self.name.text() == '':
            self.status.setText('Не указано наименование')
            return None
        elif not (self.radioCount.isChecked() or self.radioMass.isChecked()):
            self.status.setText('Не указан тип товара')
        if self.id_ is None:
            self.sender_.db.cursor().execute(
                "INSERT INTO items(name, cost, type) VALUES (?, ?, ?)",
                (self.name.text(), self.cost.value(), int(self.radioMass.isChecked())))
        else:
            self.sender_.db.cursor().execute(
                "UPDATE items SET name = ?, cost = ?, type = ? WHERE id = ?",
                (self.name.text(), self.cost.value(), int(self.radioMass.isChecked()), self.id_))
        self.sender_.db.commit()
        self.close()


class UserDialog(QDialog, Ui_userDialog):
    def __init__(self, sender):
        super().__init__()
        self.id_ = None
        self.setupUi(self)
        self.sender_ = sender
        self.canRegister.clicked.connect(self.checked)
        self.canStorage.clicked.connect(self.checked)
        self.btnSave.clicked.connect(self.save)
        self.btnCancel.clicked.connect(self.cancel)

    def get(self, id_, login, password, name, surname, rules):
        self.id_ = id_
        self.login.setText(login)
        self.password.setText(password)
        self.name.setText(name)
        self.surname.setText(surname)
        self.canRegister.setChecked(bool(int(rules[0])))
        self.canRegisterDel.setChecked(bool(int(rules[1])))
        self.canStorage.setChecked(bool(int(rules[2])))
        self.canStorageDel.setChecked(bool(int(rules[3])))
        self.canAdmin.setChecked(bool(int(rules[4])))
        self.checked()

    def checked(self):
        if self.canRegister.isChecked():
            self.canRegisterDel.setEnabled(True)
        else:
            self.canRegisterDel.setEnabled(False)
            self.canRegisterDel.setChecked(False)
        if self.canStorage.isChecked():
            self.canStorageDel.setEnabled(True)
        else:
            self.canStorageDel.setEnabled(False)
            self.canStorageDel.setChecked(False)

    def cancel(self):
        self.close()

    def save(self):
        self.checked()
        if self.login.text() == '':
            self.status.setText('Не указан логин')
            return None
        elif self.password.text() == '':
            self.status.setText('Не указан пароль')
            return None
        elif self.surname.text() == '':
            self.status.setText('Не указана фамилия')
            return None
        elif self.name.text() == '':
            self.status.setText('Не указано имя')
            return None
        elif not (self.canRegister.isChecked() or self.canStorage.isChecked() or self.canAdmin.isChecked()):
            self.status.setText('Не указаны права')
            return None
        rules = (f'{int(self.canRegister.isChecked())}{int(self.canRegisterDel.isChecked())}'
                 f'{int(self.canStorage.isChecked())}{int(self.canStorageDel.isChecked())}'
                 f'{int(self.canAdmin.isChecked())}')
        if self.id_ is None:
            self.sender_.db.cursor().execute(
                "INSERT INTO users(login, password, rules, name, surname) VALUES (?, ?, ?, ?, ?)",
                (self.login.text(), self.password.text(), rules, self.name.text(), self.surname.text()))
        else:
            self.sender_.db.cursor().execute(
                "UPDATE users SET login = ?, password = ?, rules = ?, name = ?, surname = ? WHERE id = ?",
                (self.login.text(), self.password.text(), rules, self.name.text(), self.surname.text(), self.id_))
        self.sender_.db.commit()
        self.close()


class LoginDialog(QDialog, Ui_loginDialog):
    def __init__(self, sender):
        super().__init__()
        self.setupUi(self)
        self.sender_ = sender
        with open('config.json', 'r') as f:
            self.inf = json.load(f)
            self.checkBox.setChecked(self.inf['db']['save'])
            self.dbAdress.setText(self.inf['db']['adress'])
        self.dbView.clicked.connect(self.db_view)
        self.loginButton.clicked.connect(self.login_)

    def db_view(self):
        self.dbAdress.setText(QFileDialog.getOpenFileName(self, 'Выбрать', 'C:/', 'База данных (*.sqlite);;Все файлы '
                                                                                  '(*)')[0])

    def login_(self):
        try:
            db = sqlite3.connect(self.dbAdress.text())
            cur = db.cursor()
            ans = cur.execute(
                f"SELECT * FROM users WHERE login='{self.login.text()}' and password='{self.password.text()}'"
            ).fetchall()
        except sqlite3.Error:
            self.status.setText('Ошибка базы данных')
            return None
        if len(ans) < 1:
            self.status.setText('Неверный логин или пароль')
            return None
        elif len(ans) > 1:
            self.status.setText('В базе данных несколько одинаковых пользователей')
            return None
        self.sender_.user = ans[0]
        self.sender_.db = db
        with open('config.json', 'w') as f:
            self.inf['db']['adress'] = self.dbAdress.text()
            self.inf['db']['save'] = self.checkBox.isChecked()
            json.dump(self.inf, f)
        self.close()


class App(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.temp = None
        self.user = None
        self.d = LoginDialog(self)
        self.d.show()
        self.d.exec()
        self.show()
        if self.user is None:
            sys.exit()
        self.mode_selecter.currentChanged.connect(self.mode_changed)
        self.user_add.clicked.connect(self.add_user)
        self.user_del.clicked.connect(self.del_user)
        self.user_change.clicked.connect(self.edit_user)
        self.item_add.clicked.connect(self.add_item)
        self.item_del.clicked.connect(self.del_item)
        self.item_change.clicked.connect(self.edit_item)
        self.storage_add.clicked.connect(self.add_storage)
        self.storage_del.clicked.connect(self.del_storage)
        self.storage_delall.clicked.connect(self.del_all_storage)
        self.storage_done.clicked.connect(self.done_storage)
        self.btn_add.clicked.connect(self.add_register)
        self.btn_del.clicked.connect(self.del_register)
        self.btn_delall.clicked.connect(self.del_all_register)
        self.btn_sale.clicked.connect(self.done_register)
        self.cur_mode = None
        self.check_rules()
        self.users_data()
        self.items_data()
        self.storage_data()
        self.register_data()

    def check_rules(self):
        ur = self.user[3]
        if int(ur[0]):
            self.mode_selecter.setCurrentIndex(0)
            self.cur_mode = 0
        elif int(ur[2]):
            self.mode_selecter.setCurrentIndex(1)
            self.cur_mode = 1
        elif int(ur[4]):
            self.mode_selecter.setCurrentIndex(2)
            self.cur_mode = 2

    def users_data(self):
        res = self.db.cursor().execute("SELECT id, surname, name, login, password, rules FROM users").fetchall()
        self.table_users.setRowCount(0)
        for i, row in enumerate(res):
            self.table_users.setRowCount(
                self.table_users.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table_users.setItem(
                    i, j, QTableWidgetItem(str(elem)))

    def items_data(self):
        res = self.db.cursor().execute("SELECT id, name, cost, type FROM items").fetchall()
        self.table_items.setRowCount(0)
        for i, row in enumerate(res):
            self.table_items.setRowCount(
                self.table_items.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table_items.setItem(
                    i, j, QTableWidgetItem(str(elem)))

    def storage_data(self):
        res = self.db.cursor().execute("SELECT name, amount FROM items").fetchall()
        self.table_storage.setRowCount(0)
        for i, row in enumerate(res):
            self.table_storage.setRowCount(
                self.table_storage.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table_storage.setItem(
                    i, j, QTableWidgetItem(str(elem)))

    def register_data(self):
        s = 0
        for i in range(self.table_sale.rowCount()):
            s += float(self.table_sale.item(i, 3).text())
        self.label_sum.setText(str(s))

    def closeEvent(self, event):
        self.db.close()

    def mode_changed(self):
        if int(self.user[3][self.mode_selecter.currentIndex() * 2]):
            self.cur_mode = self.mode_selecter.currentIndex()
        else:
            self.mode_selecter.setCurrentIndex(self.cur_mode)

    def add_user(self):
        d = UserDialog(self)
        d.show()
        d.exec()
        self.users_data()

    def del_user(self):
        rows = list(set([i.row() for i in self.table_users.selectedItems()]))
        ids = [self.table_users.item(i, 0).text() for i in rows]
        valid = QMessageBox.question(
            self, 'Удаление', 'Вы уверены?', QMessageBox.Yes, QMessageBox.No)
        if valid == QMessageBox.Yes:
            cur = self.db.cursor()
            cur.execute("DELETE FROM users WHERE id IN (" + ", ".join('?' * len(ids)) + ")", ids)
            self.db.commit()
        self.users_data()

    def edit_user(self):
        try:
            row = self.table_users.selectedItems()[0].row()
        except IndexError:
            return None
        d = UserDialog(self)
        d.get(self.table_users.item(row, 0).text(), self.table_users.item(row, 3).text(),
              self.table_users.item(row, 4).text(), self.table_users.item(row, 2).text(),
              self.table_users.item(row, 1).text(), self.table_users.item(row, 5).text())
        d.exec()
        self.users_data()

    def add_item(self):
        d = ItemDialog(self)
        d.show()
        d.exec()
        self.items_data()

    def del_item(self):
        rows = list(set([i.row() for i in self.table_items.selectedItems()]))
        ids = [self.table_items.item(i, 0).text() for i in rows]
        valid = QMessageBox.question(
            self, 'Удаление', 'Вы уверены?', QMessageBox.Yes, QMessageBox.No)
        if valid == QMessageBox.Yes:
            cur = self.db.cursor()
            cur.execute("DELETE FROM items WHERE id IN (" + ", ".join('?' * len(ids)) + ")", ids)
            self.db.commit()
        self.items_data()

    def edit_item(self):
        try:
            row = self.table_items.selectedItems()[0].row()
        except IndexError:
            return None
        d = ItemDialog(self)
        d.get(self.table_items.item(row, 0).text(), self.table_items.item(row, 1).text(),
              self.table_items.item(row, 2).text(), self.table_items.item(row, 3).text())
        d.exec()
        self.items_data()

    def add_storage(self):
        d = ItemSelectDialog(self)
        d.show()
        d.exec()
        if self.temp is None:
            return None
        r = ttl(self.table_storageNew, [self.temp])
        self.table_storageNew.setRowCount(0)
        for i, row in enumerate(r):
            self.table_storageNew.setRowCount(self.table_storageNew.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table_storageNew.setItem(i, j, QTableWidgetItem(str(elem)))

    def del_storage(self):
        for i in list(set([i.row() for i in self.table_storageNew.selectedItems()])):
            self.table_storageNew.removeRow(i)

    def del_all_storage(self):
        self.table_storageNew.setRowCount(0)

    def done_storage(self):
        r = {self.table_storageNew.item(i, 0).text(): float(self.table_storageNew.item(i, 1).text()) for i in
             range(self.table_storageNew.rowCount())}
        for i in r:
            q = self.db.cursor().execute("SELECT amount FROM items WHERE name = ?", (i,)).fetchall()
            r[i] += q[0][0]
        for i in r:
            self.db.cursor().execute("UPDATE items SET amount = ? WHERE name = ?", (r[i], i))
        self.db.commit()
        self.storage_data()
        self.table_storageNew.setRowCount(0)
        QMessageBox.question(self, 'Новое поступление', 'Успешно', QMessageBox.Ok)

    def add_register(self):
        d = ItemSelectDialog(self)
        d.show()
        d.exec()
        if self.temp is None:
            return None
        r = self.db.cursor().execute("SELECT cost FROM items WHERE name = ?", (self.temp[0],)).fetchall()
        self.temp = (self.temp[0], self.temp[1], r[0][0], self.temp[1] * r[0][0])
        r = ttl(self.table_sale, [self.temp])
        self.table_sale.setRowCount(0)
        for i, row in enumerate(r):
            self.table_sale.setRowCount(
                self.table_sale.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table_sale.setItem(
                    i, j, QTableWidgetItem(str(elem)))
        self.register_data()

    def del_register(self):
        for i in list(set([i.row() for i in self.table_sale.selectedItems()])):
            self.table_sale.removeRow(i)
        self.register_data()

    def del_all_register(self):
        self.table_sale.setRowCount(0)
        self.register_data()

    def done_register(self):
        r = {self.table_sale.item(i, 0).text(): float(self.table_sale.item(i, 1).text()) for i in
             range(self.table_sale.rowCount())}
        for i in r:
            q = self.db.cursor().execute("SELECT amount FROM items WHERE name = ?", (i,)).fetchall()
            r[i] = q[0][0] - r[i]
        for i in r:
            self.db.cursor().execute("UPDATE items SET amount = ? WHERE name = ?", (r[i], i))
        n = self.db.cursor().execute("SELECT checkId FROM store").fetchall()[0][0] + 1
        self.db.cursor().execute("UPDATE store SET checkId = ?", (n,))
        self.db.commit()
        self.storage_data()
        d = []
        for i in range(self.table_sale.rowCount()):
            d.append(f'{self.table_sale.item(i, 0).text()}\t{self.table_sale.item(i, 1).text()} * '
                     f'{self.table_sale.item(i, 2).text()} = {self.table_sale.item(i, 3).text()}\n')
        d = '---\n'.join(d)
        dt = datetime.now().strftime('%d.%m.%Y %H:%M')
        c = f'{dt}\nЧек №{n}\n----------\n{d}----------\nИТОГ: {self.label_sum.text()}'
        with open('config.json', 'r') as f:
            p = json.load(f)['check_path']  # type: str
            while '%username%' in p:
                p = p.replace('%username%', getenv('username'))
        with open(f'{p}/{n}.txt', 'w') as f:
            print(c)
            f.write(c)
        QMessageBox.question(self, 'Касса', 'Успешно\nЧек сохранён', QMessageBox.Ok)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = App()
    sys.excepthook = except_hook
    sys.exit(app.exec())
