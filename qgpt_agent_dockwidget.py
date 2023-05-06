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
        email                : momaabna2019@uofk.edu
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
import subprocess
import io
import contextlib
import platform
import traceback
import qgis.utils
import tempfile
from qgis.utils import *
from PyQt5.QtCore import QThread, pyqtSignal

version =qgis.utils.Qgis.QGIS_VERSION 
from qgis.PyQt.QtCore import QThreadPool
from qgis.PyQt.QtWidgets import QLabel
from .prompts import *

def containerize_code(code_string):
    code_string ="""from qgis.core import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
""" +code_string
    # From Engshell
    try:
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            exec(code_string, globals())
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.extract_tb(exc_traceback)
        filename, line, func, text = tb[-1]
        error_msg = f"{exc_type.__name__}: {str(e)}"
        return False, f'Error: {error_msg}. Getting the error from function: {func} (line: {line})'
    code_printout = output_buffer.getvalue()
    return True, code_printout
def get_completion(prompt,api_key,temprature=0.0):

    # Replace MODEL_ID with the ID of the OpenAI model you want to use
    model_id = 'text-davinci-003'
    max_tockens = 1000

    # Define the parameters for the API request
    data = {
        'model': model_id,
        'prompt': prompt,
        "max_tokens": max_tockens,
        "temperature": temprature,
        }

    # Define the headers for the API request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    try:
        # Send the API request and get the response
        response = requests.post('https://api.openai.com/v1/completions', json=data, headers=headers)
        #print(response)
        if response.status_code==200:
            
            # Parse the response to get the text completion
            completion = response.json()['choices'][0]['text']
        else:
            completion =''
    except:
        completion=''
    return completion


class RequestWorker(QThread):
    # Define a custom signal to emit when the request is finished
    finished_signal = pyqtSignal(str)
    
    def __init__(self, prompt,api_key,temprature=0.0):
        super().__init__()
        self.prompt=prompt
        self.api_key =api_key
        self.temprature=temprature
    
    def run(self):
        completion =get_completion(self.prompt, self.api_key,self.temprature)
        self.finished_signal.emit(completion)







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
        self.python_code =''
        self.command =''
        self.python_code_history =[]
        self.is_waiting =False
        self.is_debug =False
        self.agentName ='QGPT Agent'
        self.chat_text ='QGPT Agent  at Your Service  '
        self.mode =self.agentRadio.isChecked()
        try:
            self.apiTocken = os.environ['QGPT_AGENT_OPEN_AI_TOCKEN']
            self.tockenEdit.setText(self.apiTocken)
        except:
            os.environ['QGPT_AGENT_OPEN_AI_TOCKEN']=''
            self.apiTocken = os.environ['QGPT_AGENT_OPEN_AI_TOCKEN']
        try:

            self.userName =os.environ['QGPT_AGENT_USER']
            self.self.userEdit.setText(self.userName)
        except:
            os.environ['QGPT_AGENT_USER']=os.getlogin()
            self.userName =os.environ['QGPT_AGENT_USER']
            self.userEdit.setText(self.userName)


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
    
        self.update_chat()

    def select_code(self,item):
        index = self.codeList.indexFromItem(item).row()
        self.codeEdit.setText(self.python_code_history[index]['code'])

    def run_code_button(self):
        try:
            exec(self.codeEdit.toPlainText())
            print('Running code ..')
        except:
            print('Error happened while execution. ')
    def update_code(self):
        self.python_code=self.codeEdit.toPlainText()

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
    
    def update_chat(self):
        self.chatEdit.setText(self.chat_text)
        self.chatEdit.verticalScrollBar().setValue(self.chatEdit.verticalScrollBar().maximum())
        self.codeList.clear()
        self.codeList.addItems([i['title'] for i in self.python_code_history])
    def run_python_code(self):
        
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'
        st,msg=containerize_code(self.python_code)
        #print('run python',st,msg)
        if st:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        else:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
            # Correcting code to start and run it again
            prompt = make_debug_prompt(self.python_code,msg)
                #print(prompt)
            #completion = get_completion(prompt, self.apiTocken)
            self.worker = RequestWorker(prompt, self.apiTocken)
            self.worker.finished_signal.connect(self.debug_code)

            # Add the worker to a QThreadPool and start it
            
            self.worker.run()
        #self.python_code=''
        self.msgEdit.setText('')
        self.is_waiting =False
        self.update_chat()
    def debug_python_code(self):
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Compiling New Code.'
        if self.seeCodeCheckBox.isChecked():
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Edited Code :\n'+code
            self.update_chat()
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Running Code.'
        st,msg=containerize_code(self.python_code)
        if st:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        else:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        self.update_chat()
        #self.python_code=''
        self.msgEdit.setText('')
        self.is_debug =False
        self.update_chat()

    def send(self):
        #check if there is text 
        # 
        #print('send')
        if self.msgEdit.text() =='':
            return
        
        if (self.msgEdit.text() =='y' or self.msgEdit.text() =='Y') and self.is_waiting :
            self.run_python_code()
            #print('run code')
            return
        if (self.msgEdit.text() =='y' or self.msgEdit.text() =='Y') and self.is_debug :
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
        if self.mode:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Processing Your Order ...'
            self.update_chat()
            prompt = make_prompt(self.msgEdit.text())
            #print(prompt)
            #completion = get_completion()
            self.worker = RequestWorker(prompt, self.apiTocken)
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
            self.chat_text =self.chat_text+'\n'+self.agentName +' : '+self.msgEdit.text()
            prompt = make_chat_prompt(self.msgEdit.text())
            #completion = get_completion(prompt, self.apiTocken)
            worker = RequestWorker(prompt, self.apiTocken,temprature=0.7)
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
        if completion=='':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Cannot Connect to OpenAI')
            return
        self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Compiling Code.'
        code = completion.split('[[[')[1].split(']]]')[0]
        self.python_code_history.append({'title':self.command,'code':code})
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
            self.worker = RequestWorker(prompt, self.apiTocken)
            self.worker.finished_signal.connect(self.debug_code)

            # Add the worker to a QThreadPool and start it
            
            self.worker.run()
            
    
    def debug_code(self,completion):
        if completion=='':
            QtWidgets.QMessageBox.warning(self, 'Error', 'Cannot Connect to OpenAI')
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
        if st:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Done.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        else:
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Found some prblems while execution.'
            self.chat_text =self.chat_text+'\n'+self.agentName +' : ' +'Output by system :\n'+msg
        self.update_chat()

    def check_mode(self):
        self.mode =self.agentRadio.isChecked()
        #print((self.mode))

    def set_tocken(self):
        os.environ['QGPT_AGENT_OPEN_AI_TOCKEN'] =self.tockenEdit.text()
        self.apiTocken = os.environ['QGPT_AGENT_OPEN_AI_TOCKEN']
        #print(os.environ['QGPT_AGENT_OPEN_AI_TOCKEN'])
    def set_user(self):
        os.environ['QGPT_AGENT_USER'] =self.userEdit.text()

        self.userName =os.environ['QGPT_AGENT_USER']
        #print(os.environ['QGPT_AGENT_USER'])


        
    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
