from nbgrader_to_canvas.canvas import NbgraderCanvas, Token
from nbgrader_to_canvas.models import Users
from canvasapi import Canvas
from flask import session
import unittest
import pytest
import time
from nbgrader_to_canvas import db, app

class TestUploadGrades(unittest.TestCase):

    def test_init_course(self):
        assert False

    def test_get_canvas_students(self):
        assert False

    