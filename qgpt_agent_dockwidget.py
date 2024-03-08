# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGPTAgentDockWidget
                                 A QGIS plugin
 QGPT Agent is LLM Assistant that uses openai GPT model to automate QGIS processes
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-04-27
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Mohammed Nasser
        email                : momaabna2019@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import subprocess
import sys

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
import requests
import processing
import io
import contextlib
import platform
import traceback
import qgis.utils
import tempfile
from qgis.utils import *
from PyQt5.QtCore import QThread, pyqtSignal
import sqlite3
version =qgis.utils.Qgis.QGIS_VERSION 
from qgis.PyQt.QtCore import QThreadPool
from qgis.PyQt.QtWidgets import QLabel
from .prompts import *
from .functional import *
import datetime




FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgpt_agent_dockwidget_base.ui'))


class QGPTAgentDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(QGPTAgentDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        #check if the user is using the right version of QGIS
        if version[0] !='3':
            self.chat_text ='QGPT Agent  is only compatible with QGIS 3.0 and above'
            self.chatEdit.setText(self.chat_text)
            self.chatEdit.setStyleSheet("background-color: red; color: white")
            self.chatEdit.setReadOnly(True)
            return
        #check if there is no database
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'qgpt_agent.db')):
            #create database
            self.create_database()
            db =Database(os.path.join(os.path.dirname(__file__), 'qgpt_agent.db'))
            
            #connect to database
            db.connect()
            #create all tables
            db.createAllTables()
            #close connection
            db.close()
        #connect to database
        self.db =Database(os.path.join(os.path.dirname(__file__), 'qgpt_agent.db'))
        self.db.connect()





        self.python_code =''
        self.command =''
        #print(self.db.getHistory())
        self.python_code_history =[{'id':i[0],'title':i[1],'code':i[2],'datetime':i[3]} for i in self.db.getHistory()]
        self.is_waiting =False
        self.is_debug =False
        self.agentName ='QGPT Agent'
        self.chat_text ='QGPT Agent  at Your Service  '
        self.mode =self.agentRadio.isChecked()
        try:
            self.apiTocken = self.db.getSettingsValue(key='openai_tocken')
            self.tockenEdit.setText(self.apiTocken)
        except:
            self.apiTocken = ''
            self.tockenEdit.setText(self.apiTocken)
        try:

            self.userName = self.db.getSettingsValue(key='user_name')
            self.userEdit.setText(self.userName)
        except:
            self.userName =os.getlogin()
            self.db.setSettingsValue(key='user_name',value=self.userName)
            self.userEdit.setText(self.userName)
        try:
            self.chatTemperature = self.db.getSettingsValue(key='chat_temperature')
            self.tempComboBox.setCurrentIndex(int(self.chatTemperature))
        except:
            self.chatTemperature = 0.5
            self.db.setSettingsValue(key='chat_temperature',value=self.chatTemperature)
            self.tempComboBox.setCurrentIndex(int(self.chatTemperature))
        try:
            self.runPrompt = self.db.getSettingsValue(key='run_prompt')
            self.promptComboBox.setCurrentIndex(int(self.runPrompt))
        except:
            self.runPrompt = 0
            self.db.setSettingsValue(key='run_prompt',value=self.runPrompt)
            self.promptComboBox.setCurrentIndex(int(self.runPrompt))


        self.setTockenButton.clicked.connect(self.set_tocken)
        self.setUserButton.clicked.connect(self.set_user)
        self.agentRadio.clicked.connect(self.check_mode)
        self.chatRadio.clicked.connect(self.check_mode)
        self.sendButton.clicked.connect(self.send)
        self.msgEdit.returnPressed.connect(self.send)
        self.getCodeButton.clicked.connect(self.get_code)
        self.updateButton.clicked.connect(self.update_code)
        self.codeList.itemDoubleClicked.connect(self.select_code)
        self.runButton.clicked.connect(self.run_code_button)
        self.clearButton.clicked.connect(self.delete_all_history)
        self.deleteButton.clicked.connect(self.delete_history)
        self.clearChatButton.clicked.connect(self.clear_chat)
        self.docLabel.setOpenExternalLinks(True)
    
        self.update_chat()

    def create_database(self):
        with open(os.path.join(os.path.dirname(__file__), 'qgpt_agent.db'),'w') as f:
            f.close()
            

    def select_code(self,item):
        index = self.codeList.indexFromItem(item).row()
        self.codeEdit.setText(self.python_code_history[index]['code'])

    def run_code_button(self):
        try:
            print('Running code ..')
            exec(self.codeEdit.toPlainText())
            
        except:
            print('Error happened while execution. ')
    def update_code(self):
        if self.is_debug or self.is_waiting:
            self.python_code=self.codeEdit.toPlainText()
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Updated Code :\n'+self.python_code
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Send y/Y to run code n/N to cancel.'
            self.update_chat()
            QtWidgets.QMessageBox.information(self, 'Success', 'Code Updated Successfully')
        else:
            pass

        return
    def get_code(self):
        self.codeEdit.setText(self.python_code)
        return

    def install_library(self):
        try:
            print('Start installing OpenAI Library ...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openai'])
            print('installed Successfully.')
        except subprocess.CalledProcessError:
            print("Installation failed.")
    def update_history(self):
        self.python_code_history =[{'id':i[0],'title':i[1],'code':i[2],'datetime':i[3]} for i in self.db.getHistory()]
        self.update_chat()
    def clear_chat(self):
        self.chat_text ='QGPT Agent  at Your Service  '
        self.update_chat()
    def delete_all_history(self):
        #confirm delete
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Are you sure to delete all history?", QtWidgets.QMessageBox.Yes | 
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.db.deleteAllHistory()
            self.update_history()
            QtWidgets.QMessageBox.information(self, 'Success', 'History Deleted Successfully')
    def delete_history(self):
        index = self.codeList.currentRow() 
        #confirm delete
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Are you sure to delete this history?", QtWidgets.QMessageBox.Yes | 
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.db.deleteHistory(id=self.python_code_history[index]['id'])
            self.update_history()
            QtWidgets.QMessageBox.information(self, 'Success', 'History Deleted Successfully')
    def update_chat(self):
        self.chatEdit.setText(self.chat_text)
        self.chatEdit.verticalScrollBar().setValue(self.chatEdit.verticalScrollBar().maximum())
        self.codeList.clear()
        self.codeList.addItems([i['title'] for i in self.python_code_history])
    
    def run_python_code_result(self,result):#result is success+|||+print_output
        success= result.split('|||')[0]
        print_output =result.split('|||')[1]
        self.db.addHistory(command=self.command,code=self.python_code,datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),success=success,printout=print_output)
        self.update_history()
        if success=='True':
            #print(success)
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+print_output
        else:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+print_output
            # Correcting code to start and run it again
            prompt = make_debug_prompt(self.python_code, print_output)
                #print(prompt)
            #completion = get_completion(prompt, self.apiTocken)
            self.worker = RequestWorker(prompt)
            self.worker.finished_signal.connect(self.debug_code)

            # Add the worker to a QThreadPool and start it
            
            self.worker.run()
            self.update_chat()
        #self.python_code=''
        self.msgEdit.setText('')
        self.is_waiting =False
        self.update_chat()



    def run_python_code(self):
        
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'
        #st,msg=containerize_code(self.python_code)
        #print('run python',st,msg)
        self.worker = CodeRunner(code_string=self.python_code)
        self.worker.finished_signal.connect(self.run_python_code_result)
        self.worker.run()
        self.is_waiting =False
        self.update_chat()
        #self.python_code=''

    def debug_python_code_result(self,result):#result is success+|||+print_output
        success= result.split('|||')[0]
        print_output =result.split('|||')[1]
        
        self.db.addHistory(self.command, self.python_code, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), success, print_output)
        self.update_history()
        if success=='True':
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+print_output
        else:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+print_output
        self.update_chat()
        #self.python_code=''
        self.msgEdit.setText('')
        self.is_debug =False
        self.update_chat()


    def debug_python_code(self):
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Compiling New Code.'
        if self.seeCodeCheckBox.isChecked():
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Edited Code :\n'+code
            self.update_chat()
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'

        #st,msg=containerize_code(self.python_code)
        #print('run python',st,msg)
        self.worker = CodeRunner(code_string=self.python_code)
        self.worker.finished_signal.connect(self.debug_python_code_result)
        self.worker.run()
        self.is_debug =False
        self.update_chat()
        #self.python_code=''
        
    def send(self):
        #check if there is text 
        # 
        #print('send')
        if self.msgEdit.text() =='':
            return
        
        if (self.msgEdit.text() =='y' or self.msgEdit.text() =='Y') and self.is_waiting :
            self.chat_text =self.chat_text+'\n'+self.userName +' : ' +self.msgEdit.text()
            self.msgEdit.setText('')
            self.update_chat()
            self.run_python_code()
            #print('run code')
            return
        if (self.msgEdit.text() =='y' or self.msgEdit.text() =='Y') and self.is_debug :
            self.chat_text =self.chat_text+'\n'+self.userName +' : ' +self.msgEdit.text()
            self.msgEdit.setText('')
            self.update_chat()
            self.debug_python_code()
            return
        if (self.msgEdit.text() =='n' or self.msgEdit.text() =='N'):
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Process Canceled.'
            self.python_code=''
            self.msgEdit.setText('')
            self.is_debug =False
            self.is_waiting=False
            self.update_chat()
            return
        if self.is_debug or self.is_waiting:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Please Enter Y/y or N/n.'
            self.update_chat()
            return
        self.command =self.msgEdit.text()
        self.chat_text =self.chat_text+'\n'+self.userName +' : ' +self.msgEdit.text()
        self.msgEdit.setText('')
        self.update_chat()
        if self.mode:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Processing Your Order ...'
            self.update_chat()
            prompt = make_prompt(self.runPrompt)
            #print(prompt)
            #completion = get_completion()
            self.worker = RequestWorker(self.command)
            self.worker.finished_signal.connect(self.run_code)

            # Add the worker to a QThreadPool and start it
            self.worker.run()
            """ self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Compiling Code.'
            code = completion.split('[[[')[1].split(']]]')[0]
            if self.seeCodeCheckBox.isChecked():
                self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Code :\n'+code
                self.update_chat()

            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'
            st,msg=containerize_code(code)
            if st:
                self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
                self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
            else:
                self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
                self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
                # Correcting code to start and run it again
                prompt = make_debug_prompt(code,msg)
                #print(prompt)
                completion = get_completion(prompt, self.apiTocken)
                msg =completion.split('[[[')[1].split(']]]')[0]
                code = completion.split('[[[')[2].split(']]]')[0]
                self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Compiling New Code.'
                if self.seeCodeCheckBox.isChecked():
                    self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Edited Code :\n'+code
                    self.update_chat()
                self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'
                st,msg=containerize_code(code)
                if st:
                    self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
                    self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
                else:
                    self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
                    self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
            self.update_chat() """

        else:
            #self.chat_text =self.chat_text+'\n'+self.agentName +' : '+self.msgEdit.text()
            prompt = make_chat_prompt()
            #completion = get_completion(prompt, self.apiTocken)
            worker = RequestWorker(self.command)
            worker.finished_signal.connect(self.run_chat)
            # Add the worker to a QThreadPool and start it
            worker.run()
            #self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +completion

        self.msgEdit.setText('')
        self.update_chat()
    #chat
    def run_chat(self,completion):
        if completion=='':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Cannot Connect to OpenAI')
            return
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +completion.strip()
    #code executions
    def run_code(self,completion):
        if completion=='connection_error':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Cannot Connect to OpenAI')
            return
        if completion=='code_error':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Cannot retrieve dat from OpenAI plaease check your API key and Balance')
            return
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Compiling Code.'
        #print(completion)
        code = completion.split('[[[')[1].split(']]]')[0]
        
        self.python_code_history.append({'title':self.command,'code':code,'datetime':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        if self.seeCodeCheckBox.isChecked():
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Code :\n'+code
            self.update_chat()
        if not self.runCheckBox.isChecked():
            self.python_code = code
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Code :\n'+code
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Send y/Y to run code n/N to cancel.'
            self.update_chat()
            self.is_waiting =True
            return
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'
        st,msg=containerize_code(code)
        self.db.addHistory(command=self.command,code=code,datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),success=str(st),printout=msg)
        self.update_history()
        if st:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        else:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
            # Correcting code to start and run it again
            prompt = make_debug_prompt(code,msg)
                #print(prompt)
            #completion = get_completion(prompt, self.apiTocken)
            self.worker = RequestWorker(prompt)
            self.worker.finished_signal.connect(self.debug_code)

            # Add the worker to a QThreadPool and start it
            
            self.worker.run()
            
    
    def debug_code(self,completion):
        #print('com: ',completion)
        if completion=='connection_error':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Cannot Connect to OpenAI')
            return
        if completion=='code_error':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Cannot retrieve dat from OpenAI plaease check your API key and Balance')
            return
        msg =completion.split('[[[')[1].split(']]]')[0]
        code = completion.split('[[[')[2].split(']]]')[0]
        if not self.runCheckBox.isChecked():
            self.is_debug =True
            self.python_code = code
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +msg
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Edited Code  :\n'+code
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Send y/Y to run code n/N to cancel..'
            self.update_chat()
            self.is_debug = True
            return
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +msg
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Compiling New Code.'
        if self.seeCodeCheckBox.isChecked():
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Edited Code :\n'+code
            self.update_chat()
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'
        st,msg=containerize_code(code)
        self.db.addHistory(command=self.command,code=code,datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),success=str(st),printout=msg)
        self.update_history()
        if st:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        else:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        self.update_chat()

    def check_mode(self):
        self.mode =self.agentRadio.isChecked()
        self.db.setSettingsValue('mode',str(self.mode) )
        #print((self.mode))

    def set_tocken(self):
        os.environ['QGPT_AGENT_OPEN_AI_TOCKEN'] =self.tockenEdit.text()
        #set tocken to database
        self.db.setSettingsValue('openai_tocken',self.tockenEdit.text())
        if self.tempComboBox.currentIndex() == 0:
            self.chatTemperature =0.0
        elif self.tempComboBox.currentIndex() == 1:
            self.chatTemperature =0.4
        elif self.tempComboBox.currentIndex() == 2:
            self.chatTemperature =0.7
        self.db.setSettingsValue('chat_temperature', str(self.chatTemperature))
        self.apiTocken = os.environ['QGPT_AGENT_OPEN_AI_TOCKEN']
        #print(os.environ['QGPT_AGENT_OPEN_AI_TOCKEN'])
    def set_user(self):
        os.environ['QGPT_AGENT_USER'] =self.userEdit.text()
        #set user name to database
        self.db.setSettingsValue('user_name',self.userEdit.text())
        self.db.setSettingsValue('run_prompt', str(self.promptComboBox.currentIndex()))
        self.runPrompt = self.promptComboBox.currentIndex()
        

        self.userName =os.environ['QGPT_AGENT_USER']
        #print(os.environ['QGPT_AGENT_USER'])


        
    def closeEvent(self, event):
        self.closingPlugin.emit()
        #clsoe database
        self.db.close()
        event.accept()
