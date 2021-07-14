
from nbgrader_to_canvas.canvas import CanvasWrapper
from nbgrader_to_canvas import db
from nbgrader_to_canvas.models import AssignmentMatch
import time

# Test data for test_canvas


class FakeResponse:
    def __init__(self,headers, status_code):
        self.headers = headers
        self.status_code = status_code


# Test data for test_upload_grades
canvas_students = {'testacct111': 114217, 'testacct222': 115752, 'testacct333': 115753, 'mdandrad': 54, 'matthewf': 53, 'pjamason': 52, 'jdkindley': 139640, 'e7li': 90840, 'shrakibullah': 114262, 'nb2canvas_student1': 141753, 'nb2canvas_student2': 141754, 'nb2canvas_student3': 141755, 'nb2canvas_student4': 141756, 'nb2canvas_student5': 141757, 'nb2canvas_student6': 141758, 'nb2canvas_student7': 141759, 'nb2canvas_student8': 141760, 'nb2canvas_student9': 141761, 'nb2canvas_student10': 141762, 'nb2canvas_student11': 141763, 'nb2canvas_student12': 141764, 'nb2canvas_student13': 141765, 'nb2canvas_student14': 141766, 'nb2canvas_student15': 141767, 'nb2canvas_student16': 141768, 'nb2canvas_student17': 141769, 'nb2canvas_student18': 141770, 'nb2canvas_student19': 141771, 'nb2canvas_student20': 141772, 'nb2canvas_student21': 141773, 'nb2canvas_student22': 141774, 'nb2canvas_student23': 141775, 'nb2canvas_student24': 141776, 'nb2canvas_student25': 141777, 'nb2canvas_student26': 141778, 'nb2canvas_student27': 141779, 'nb2canvas_student28': 141780, 'nb2canvas_student29': 141781, 'nb2canvas_student30': 141782, 'nb2canvas_student31': 141783, 'nb2canvas_student32': 141784, 'nb2canvas_student33': 141785, 'nb2canvas_student34': 141786, 'nb2canvas_student35': 141787, 'nb2canvas_student36': 141788, 'nb2canvas_student37': 141789, 'nb2canvas_student38': 141790, 'nb2canvas_student39': 141791, 'nb2canvas_student40': 141792, 'nb2canvas_student41': 141793, 'nb2canvas_student42': 141794, 'nb2canvas_student43': 141795, 'nb2canvas_student44': 141796, 'nb2canvas_student45': 141797, 'nb2canvas_student46': 141798, 'nb2canvas_student47': 141799, 'nb2canvas_student48': 141800, 'nb2canvas_student49': 141801, 'nb2canvas_student50': 141802, 'nb2canvas_student51': 141803, 'nb2canvas_student52': 141804, 'nb2canvas_student53': 141805, 'nb2canvas_student54': 141806, 'nb2canvas_student55': 141807, 'nb2canvas_student56': 141808, 'nb2canvas_student57': 141809, 'nb2canvas_student58': 141810, 'nb2canvas_student59': 141811, 'nb2canvas_student60': 141812, 'nb2canvas_student61': 141813, 'nb2canvas_student62': 141814, 'nb2canvas_student63': 141815, 'nb2canvas_student64': 141816, 'nb2canvas_student65': 141817, 'nb2canvas_student66': 141818, 'nb2canvas_student67': 141819, 'nb2canvas_student68': 141820, 'nb2canvas_student69': 141821, 'nb2canvas_student70': 141822, 'nb2canvas_student71': 141823, 'nb2canvas_student72': 141824, 'nb2canvas_student73': 141825, 'nb2canvas_student74': 141826, 'nb2canvas_student75': 141827, 'nb2canvas_student76': 141828, 'nb2canvas_student77': 141829, 'nb2canvas_student78': 141830, 'nb2canvas_student79': 141831, 'nb2canvas_student80': 141832, 'nb2canvas_student81': 141833, 'nb2canvas_student82': 141834, 'nb2canvas_student83': 141835, 'nb2canvas_student84': 141836, 'nb2canvas_student85': 141837, 'nb2canvas_student86': 141838, 'nb2canvas_student87': 141839, 'nb2canvas_student88': 141840, 'nb2canvas_student89': 141841, 'nb2canvas_student90': 141842, 'nb2canvas_student91': 141843, 'nb2canvas_student92': 141844, 'nb2canvas_student93': 141845, 'nb2canvas_student94': 141846, 'nb2canvas_student95': 141847, 'nb2canvas_student96': 141848, 'nb2canvas_student97': 141849, 'nb2canvas_student98': 141850, 'nb2canvas_student99': 141851, 'nb2canvas_student100': 141852, 'nb2canvas_student101': 143120, 'nb2canvas_student102': 143121, 'nb2canvas_student103': 143122, 'nb2canvas_student104': 143123, 'nb2canvas_student105': 143124, 'nb2canvas_student106': 143125, 'nb2canvas_student107': 143126, 'nb2canvas_student108': 143127, 'nb2canvas_student109': 143128, 
'nb2canvas_student110': 143129, 'nb2canvas_student111': 143130, 'nb2canvas_student112': 143131, 'nb2canvas_student113': 143132, 'nb2canvas_student114': 143133, 'nb2canvas_student115': 143134, 'nb2canvas_student116': 143135, 'nb2canvas_student117': 143136, 'nb2canvas_student118': 143137, 'nb2canvas_student119': 143138, 'nb2canvas_student120': 143139, 'nb2canvas_student121': 143140, 'nb2canvas_student122': 143141, 'nb2canvas_student123': 143142, 'nb2canvas_student124': 143143, 'nb2canvas_student125': 143144, 'nb2canvas_student126': 143145, 'nb2canvas_student127': 143146, 'nb2canvas_student128': 143147, 'nb2canvas_student129': 143148, 'nb2canvas_student130': 143149, 'nb2canvas_student131': 143150, 'nb2canvas_student132': 143151, 'nb2canvas_student133': 143152, 'nb2canvas_student134': 143153, 'nb2canvas_student135': 143154, 'nb2canvas_student136': 143155, 'nb2canvas_student137': 143156, 'nb2canvas_student138': 143157, 'nb2canvas_student139': 143158, 'nb2canvas_student140': 143159, 'nb2canvas_student141': 143160, 'nb2canvas_student142': 143161, 'nb2canvas_student143': 143162, 'nb2canvas_student144': 143163, 'nb2canvas_student145': 143164, 'nb2canvas_student146': 143165, 'nb2canvas_student147': 143166, 'nb2canvas_student148': 143167, 'nb2canvas_student149': 143168, 'nb2canvas_student150': 143169, 'nb2canvas_student151': 143170, 'nb2canvas_student152': 143171, 'nb2canvas_student153': 143172, 'nb2canvas_student154': 143173, 'nb2canvas_student155': 143174, 'nb2canvas_student156': 143175, 'nb2canvas_student157': 143176, 'nb2canvas_student158': 143177, 'nb2canvas_student159': 143178, 'nb2canvas_student160': 143179, 'nb2canvas_student161': 143180, 'nb2canvas_student162': 143181, 'nb2canvas_student163': 143182, 'nb2canvas_student164': 143183, 'nb2canvas_student165': 143184, 'nb2canvas_student166': 143185, 'nb2canvas_student167': 143186, 'nb2canvas_student168': 143187, 'nb2canvas_student169': 143188, 'nb2canvas_student170': 143189, 'nb2canvas_student171': 143190, 'nb2canvas_student172': 143191, 'nb2canvas_student173': 143192, 'nb2canvas_student174': 143193, 'nb2canvas_student175': 143194, 'nb2canvas_student176': 143195, 'nb2canvas_student177': 143196, 'nb2canvas_student178': 143197, 'nb2canvas_student179': 143198, 'nb2canvas_student180': 143199, 'nb2canvas_student181': 143200, 'nb2canvas_student182': 143201, 'nb2canvas_student183': 143202, 'nb2canvas_student184': 143203, 'nb2canvas_student185': 143204, 'nb2canvas_student186': 143205, 'nb2canvas_student187': 143206, 'nb2canvas_student188': 143207, 'nb2canvas_student189': 143208, 'nb2canvas_student190': 143209, 'nb2canvas_student191': 143210, 'nb2canvas_student192': 143211, 'nb2canvas_student193': 143212, 'nb2canvas_student194': 143213, 'nb2canvas_student195': 143214, 'nb2canvas_student196': 143215, 'nb2canvas_student197': 143216, 'nb2canvas_student198': 143217, 'nb2canvas_student199': 143218, 'nb2canvas_student200': 143219, 'nb2canvas_student201': 143220, 'nb2canvas_student202': 143221, 'nb2canvas_student203': 143222, 'nb2canvas_student204': 143223, 'nb2canvas_student205': 143224, 'nb2canvas_student206': 143225, 'nb2canvas_student207': 143226, 'nb2canvas_student208': 143227, 'nb2canvas_student209': 143228, 'nb2canvas_student210': 143229, 'nb2canvas_student211': 143230, 'nb2canvas_student212': 143231, 'nb2canvas_student213': 143232, 'nb2canvas_student214': 143233, 'nb2canvas_student215': 143234, 'nb2canvas_student216': 143235, 'nb2canvas_student217': 143236, 'nb2canvas_student218': 143237, 'nb2canvas_student219': 143238, 'nb2canvas_student220': 143239, 'nb2canvas_student221': 143240, 'nb2canvas_student222': 143241, 'nb2canvas_student223': 143242, 'nb2canvas_student224': 143243, 'nb2canvas_student225': 143244, 'nb2canvas_student226': 143245, 'nb2canvas_student227': 143246, 'nb2canvas_student228': 143247, 'nb2canvas_student229': 143248, 'nb2canvas_student230': 143249, 'nb2canvas_student231': 143250, 'nb2canvas_student232': 143251, 'nb2canvas_student233': 143252, 'nb2canvas_student234': 143253, 'nb2canvas_student235': 143254, 'nb2canvas_student236': 143255, 'nb2canvas_student237': 143256, 'nb2canvas_student238': 143257, 'nb2canvas_student239': 143258, 'nb2canvas_student240': 143259, 'nb2canvas_student241': 143260, 'nb2canvas_student242': 143261, 'nb2canvas_student243': 143262, 'nb2canvas_student244': 143263, 'nb2canvas_student245': 143264, 'nb2canvas_student246': 143265, 'nb2canvas_student247': 143266, 'nb2canvas_student248': 143267, 'nb2canvas_student249': 143268, 'nb2canvas_student250': 143269, 'nb2canvas_student251': 143270, 'nb2canvas_student252': 143271, 'nb2canvas_student253': 143272, 'nb2canvas_student254': 143273, 'nb2canvas_student255': 143274, 'nb2canvas_student256': 143275, 'nb2canvas_student257': 143276, 'nb2canvas_student258': 143277, 'nb2canvas_student259': 143278, 'nb2canvas_student260': 143279, 'nb2canvas_student261': 143280, 'nb2canvas_student262': 143281, 'nb2canvas_student263': 143282, 'nb2canvas_student264': 143283, 'nb2canvas_student265': 143284, 'nb2canvas_student266': 143285, 'nb2canvas_student267': 143286, 'nb2canvas_student268': 143287, 'nb2canvas_student269': 143288, 'nb2canvas_student270': 143289, 'nb2canvas_student271': 143290, 'nb2canvas_student272': 143291, 'nb2canvas_student273': 143292, 'nb2canvas_student274': 143293, 'nb2canvas_student275': 143294, 'nb2canvas_student276': 143295, 'nb2canvas_student277': 143296, 'nb2canvas_student278': 143297, 'nb2canvas_student279': 143298, 'nb2canvas_student280': 143299, 'nb2canvas_student281': 143300, 'nb2canvas_student282': 143301, 'nb2canvas_student283': 143302, 'nb2canvas_student284': 143303, 'nb2canvas_student285': 143304, 'nb2canvas_student286': 143305, 'nb2canvas_student287': 143306, 'nb2canvas_student288': 143307, 'nb2canvas_student289': 143308, 'nb2canvas_student290': 143309, 'nb2canvas_student291': 143310, 'nb2canvas_student292': 143311, 'nb2canvas_student293': 143312, 'nb2canvas_student294': 143313, 'nb2canvas_student295': 143314, 'nb2canvas_student296': 143315, 'nb2canvas_student297': 143316, 'nb2canvas_student298': 143317, 'nb2canvas_student299': 143318, 'nb2canvas_student300': 143319, 'nb2canvas_student301': 143320, 'nb2canvas_student302': 143321, 'nb2canvas_student303': 143322, 'nb2canvas_student304': 143323, 'nb2canvas_student305': 143324, 'nb2canvas_student306': 143325, 'nb2canvas_student307': 143326, 'nb2canvas_student308': 143327, 'nb2canvas_student309': 143328,
'nb2canvas_student310': 143329, 'nb2canvas_student311': 143330, 'nb2canvas_student312': 143331, 'nb2canvas_student313': 143332, 'nb2canvas_student314': 143333, 'nb2canvas_student315': 143334, 'nb2canvas_student316': 143335, 'nb2canvas_student317': 143336, 'nb2canvas_student318': 143337, 'nb2canvas_student319': 143338, 'nb2canvas_student320': 143339, 'nb2canvas_student321': 143340, 'nb2canvas_student322': 143341, 'nb2canvas_student323': 143342, 'nb2canvas_student324': 143343, 'nb2canvas_student325': 143344, 'nb2canvas_student326': 143345, 'nb2canvas_student327': 143346, 'nb2canvas_student328': 143347, 'nb2canvas_student329': 143348, 'nb2canvas_student330': 143349, 'nb2canvas_student331': 143350, 'nb2canvas_student332': 143351, 'nb2canvas_student333': 143352, 'nb2canvas_student334': 143353, 'nb2canvas_student335': 143354, 'nb2canvas_student336': 143355, 'nb2canvas_student337': 143356, 'nb2canvas_student338': 143357, 'nb2canvas_student339': 143358, 'nb2canvas_student340': 143359, 'nb2canvas_student341': 143360, 'nb2canvas_student342': 143361, 'nb2canvas_student343': 143362, 'nb2canvas_student344': 143363, 'nb2canvas_student345': 143364, 'nb2canvas_student346': 143365, 'nb2canvas_student347': 143366, 'nb2canvas_student348': 143367, 'nb2canvas_student349': 143368, 'nb2canvas_student350': 143369, 'nb2canvas_student351': 143370, 'nb2canvas_student352': 143371, 'nb2canvas_student353': 143372, 'nb2canvas_student354': 143373, 'nb2canvas_student355': 143374, 'nb2canvas_student356': 143375, 'nb2canvas_student357': 143376, 'nb2canvas_student358': 143377, 'nb2canvas_student359': 143378, 'nb2canvas_student360': 143379, 'nb2canvas_student361': 143380, 'nb2canvas_student362': 143381, 'nb2canvas_student363': 143382, 'nb2canvas_student364': 143383, 'nb2canvas_student365': 143384, 'nb2canvas_student366': 143385, 'nb2canvas_student367': 143386, 'nb2canvas_student368': 143387, 'nb2canvas_student369': 143388, 'nb2canvas_student370': 143389, 'nb2canvas_student371': 143390, 'nb2canvas_student372': 143391, 'nb2canvas_student373': 143392, 'nb2canvas_student374': 143393, 'nb2canvas_student375': 143394, 'nb2canvas_student376': 143395, 'nb2canvas_student377': 143396, 'nb2canvas_student378': 143397, 'nb2canvas_student379': 143398, 'nb2canvas_student380': 143399, 'nb2canvas_student381': 143400, 'nb2canvas_student382': 143401, 'nb2canvas_student383': 143402, 'nb2canvas_student384': 143403, 'nb2canvas_student385': 143404, 'nb2canvas_student386': 143405, 'nb2canvas_student387': 143406, 'nb2canvas_student388': 143407, 'nb2canvas_student389': 143408, 'nb2canvas_student390': 143409, 'nb2canvas_student391': 143410, 'nb2canvas_student392': 143411, 'nb2canvas_student393': 143412, 'nb2canvas_student394': 143413, 'nb2canvas_student395': 143414, 'nb2canvas_student396': 143415, 'nb2canvas_student397': 143416, 'nb2canvas_student398': 143417, 'nb2canvas_student399': 143418, 'nb2canvas_student400': 143419, 'wuykimpang': 86959}

student_grades = {115753: {'posted_grade': ''}, 114262: {'posted_grade': 0.0}, 90840: {'posted_grade': 6.0}, 141755: {'posted_grade': ''}, 141753: {'posted_grade': ''}, 141754: {'posted_grade': ''}}

existing_assignment = 'Test Assignment 2'

# Test data for test_grade_overview
expected_nbgrader_assignments = {'Test Assignment 1', 'Test Assignment 3', 'Test Assignment 2', 'assign1'}
expected_canvas_assignments = {192792: 'Week 1: Assignment', 192793: 'Week 2: Assignment', 192794: 'Week 3: Assignment', 192795: 'Week 4: Assignment', 192796: 'Week 5: Assignment [Peer Review]'}
expected_matches_names = {'Test Assignment 1', 'assign1', 'Test Assignment 3', 'Test Assignment 2'}


def wipe_db():
    # clear AssignmentMatch
    for match in AssignmentMatch.query.filter_by():
        db.session.delete(match)
    # wipe Test Assignment 1-3, and assign1
    canvas_wrapper = CanvasWrapper('https://ucsd.test.instructure.com', {'canvas_user_id': '114217'})
    canvas = canvas_wrapper.get_canvas()
    course = canvas.get_course(20774)
    
    for assignment in course.get_assignments_for_group(92059):
        if not 'Week' in assignment.name:
            assignment.delete()

    db.session.commit()

def clear_grades():
    canvas_wrapper = CanvasWrapper('https://ucsd.test.instructure.com', {'canvas_user_id': '114217'})
    canvas = canvas_wrapper.get_canvas()
    course = canvas.get_course(20774)
    users = course.get_recent_students()
    clear_grades = {user.id: {'posted_grade':''} for user in users}
    for assignment in course.get_assignments_for_group(92059):
        if assignment.published:
            try:
                progress = assignment.submissions_bulk_update(grade_data=clear_grades)
                timeout = time.time()+10
                while not progress.workflow_state == 'completed' and timeout > time.time():
                    progress = progress.query()
                    time.sleep(.1)
                    if progress.workflow_state == 'failed':
                        print('failed')
                        break
                print(assignment.name, progress.workflow_state)
            except:
                print(assignment.name)
