

#TODO: Might be better practice to store these as global variables in their respective test files
# Test data for test_canvas


class FakeResponse:
    def __init__(self,headers, status_code):
        self.headers = headers
        self.status_code = status_code


# Test data for test_upload_grades
canvas_students = {'testacct111': 114217, 'testacct222': 115752, 'testacct333': 115753, 'mdandrad': 54, 'matthewf': 53, 'pjamason': 52, 'jdkindley': 139640, 'e7li': 90840, 'shrakibullah': 114262, 'nb2canvas_student1': 141753, 'nb2canvas_student2': 141754, 'nb2canvas_student3': 141755, 'nb2canvas_student4': 141756, 'nb2canvas_student5': 141757, 'nb2canvas_student6': 141758, 'nb2canvas_student7': 141759, 'nb2canvas_student8': 141760, 'nb2canvas_student9': 141761, 'nb2canvas_student10': 141762, 'nb2canvas_student11': 141763, 'nb2canvas_student12': 141764, 'nb2canvas_student13': 141765, 'nb2canvas_student14': 141766, 'nb2canvas_student15': 141767, 'nb2canvas_student16': 141768, 'nb2canvas_student17': 141769, 'nb2canvas_student18': 141770, 'nb2canvas_student19': 141771, 'nb2canvas_student20': 141772, 'nb2canvas_student21': 141773, 'nb2canvas_student22': 141774, 'nb2canvas_student23': 141775, 'nb2canvas_student24': 141776, 'nb2canvas_student25': 141777, 'nb2canvas_student26': 141778, 'nb2canvas_student27': 141779, 'nb2canvas_student28': 141780, 'nb2canvas_student29': 141781, 'nb2canvas_student30': 141782, 'nb2canvas_student31': 141783, 'nb2canvas_student32': 141784, 'nb2canvas_student33': 141785, 'nb2canvas_student34': 141786, 'nb2canvas_student35': 141787, 'nb2canvas_student36': 141788, 'nb2canvas_student37': 141789, 'nb2canvas_student38': 141790, 'nb2canvas_student39': 141791, 'nb2canvas_student40': 141792, 'nb2canvas_student41': 141793, 'nb2canvas_student42': 141794, 'nb2canvas_student43': 141795, 'nb2canvas_student44': 141796, 'nb2canvas_student45': 141797, 'nb2canvas_student46': 141798, 'nb2canvas_student47': 141799, 'nb2canvas_student48': 141800, 'nb2canvas_student49': 141801, 'nb2canvas_student50': 141802, 'nb2canvas_student51': 141803, 'nb2canvas_student52': 141804, 'nb2canvas_student53': 141805, 'nb2canvas_student54': 141806, 'nb2canvas_student55': 141807, 'nb2canvas_student56': 141808, 'nb2canvas_student57': 141809, 'nb2canvas_student58': 141810, 'nb2canvas_student59': 141811, 'nb2canvas_student60': 141812, 'nb2canvas_student61': 141813, 'nb2canvas_student62': 141814, 'nb2canvas_student63': 141815, 'nb2canvas_student64': 141816, 'nb2canvas_student65': 141817, 'nb2canvas_student66': 141818, 'nb2canvas_student67': 141819, 'nb2canvas_student68': 141820, 'nb2canvas_student69': 141821, 'nb2canvas_student70': 141822, 'nb2canvas_student71': 141823, 'nb2canvas_student72': 141824, 'nb2canvas_student73': 141825, 'nb2canvas_student74': 141826, 'nb2canvas_student75': 141827, 'nb2canvas_student76': 141828, 'nb2canvas_student77': 141829, 'nb2canvas_student78': 141830, 'nb2canvas_student79': 141831, 'nb2canvas_student80': 141832, 'nb2canvas_student81': 141833, 'nb2canvas_student82': 141834, 'nb2canvas_student83': 141835, 'nb2canvas_student84': 141836, 'nb2canvas_student85': 141837, 'nb2canvas_student86': 141838, 'nb2canvas_student87': 141839, 'nb2canvas_student88': 141840, 'nb2canvas_student89': 141841, 'nb2canvas_student90': 141842, 'nb2canvas_student91': 141843, 'nb2canvas_student92': 141844, 'nb2canvas_student93': 141845, 'nb2canvas_student94': 141846, 'nb2canvas_student95': 141847, 'nb2canvas_student96': 141848, 'nb2canvas_student97': 141849, 'nb2canvas_student98': 141850, 'nb2canvas_student99': 141851, 'nb2canvas_student100': 141852, 'wuykimpang': 86959}

student_grades = {90840: {'posted_grade': 6.0}, 114262: {'posted_grade': 0.0}}

existing_assignment = 'Test Assignment 2'

# Test data for test_grade_overview
expected_nbgrader_assignments = {'Test Assignment 1', 'Test Assignment 3', 'Test Assignment 2', 'assign1'}
expected_canvas_assignments = {192792: 'Week 1: Assignment', 192793: 'Week 2: Assignment', 192794: 'Week 3: Assignment', 192795: 'Week 4: Assignment', 192796: 'Week 5: Assignment [Peer Review]'}
expected_matches_names = {'Test Assignment 1', 'assign1', 'Test Assignment 3', 'Test Assignment 2'}
