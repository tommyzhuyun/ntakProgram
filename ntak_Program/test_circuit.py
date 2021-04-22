from unittest import TestCase

from circuit import *


class TestElement(TestCase):
    def test_print_msg(self):
        element = Element()
        element.num = 1
        element.node = {'top': 'node_top', 'bottom': 'node_bottom'}
        element.param = "element_param"

        element.print_msg("test message")


class TestResistor(TestCase):
    def test_print_element(self):
        resistor = Resistor()
        resistor.num = 1
        resistor.node = {Resistor.R_TOP: '2', Resistor.R_BOTTOM: '3'}
        resistor.param = '1k'
        resistor.print_element()
        resistor.print_node()

        resistor2 = Resistor(2, {Resistor.R_TOP: '4', Resistor.R_BOTTOM: '5'}, '2k')
        resistor2.print_element()
        resistor2.print_node()

        print(f"TestResistor.get_element_str: [{resistor2.get_element_str()}]")
        print(f"TestResistor.get_node_str: [{resistor2.get_node_str()}]")

    def test_print_node(self):
        pass


class TestCapacitor(TestCase):
    def test_print_element(self):
        capacitor = Capacitor()
        capacitor.num = 1
        capacitor.node = {Capacitor.C_TOP: '2', Capacitor.C_BOTTOM: '3'}
        capacitor.param = '0.3p'
        capacitor.print_element()
        capacitor.print_node()

        capacitor2 = Capacitor(2, {Capacitor.C_TOP: '4', Capacitor.C_BOTTOM: '5'}, '2k')
        capacitor2.print_element()
        capacitor2.print_node()

        print(f"TestCapacitor.get_element_str: [{capacitor2.get_element_str()}]")
        print(f"TestCapacitor.get_node_str: [{capacitor2.get_node_str()}]")

    def test_print_node(self):
        pass


class TestInductor(TestCase):
    def test_print_element(self):
        inductor = Inductor()
        inductor.num = 1
        inductor.node = {Inductor.L_TOP: '2', Inductor.L_BOTTOM: '3'}
        inductor.param = '400u'
        inductor.print_element()
        inductor.print_node()

        inductor2 = Inductor(2, {Inductor.L_TOP: '4', Inductor.L_BOTTOM: '5'}, '400u')
        inductor2.print_element()
        inductor2.print_node()

        print(f"TestInductor.get_element_str: [{inductor2.get_element_str()}]")
        print(f"TestInductor.get_node_str: [{inductor2.get_node_str()}]")

    def test_print_node(self):
        pass


class TestVsource(TestCase):
    def test_print_element(self):
        vsource = Vsource()
        vsource.num = 'dd'
        vsource.node = {Vsource.V_TOP: '2', Vsource.V_BOTTOM: '3'}
        vsource.param = '1.5'
        vsource.print_element()
        vsource.print_node()
        vsource.param = "dc 1.5 ac 1"
        vsource.print_element()
        vsource.print_node()
        vsource.param = "sin(0 1 1k 0 0 45.0)"
        vsource.print_element()
        vsource.print_node()
        vsource.param = "pulse(-1 1 0 1e-5 1e-5 5e-4 1e-3 45.0)"
        vsource.print_element()
        vsource.print_node()

        vsource2 = Vsource(2, {Vsource.V_TOP: '4', Vsource.V_BOTTOM: '5'}, '1.5')
        vsource2.print_element()
        vsource2.print_node()

        print(f"TestVsource.get_element_str: [{vsource.get_element_str()}]")
        print(f"TestVsource.get_node_str: [{vsource.get_node_str()}]")


class TestIsource(TestCase):
    def test_print_element(self):
        isource = Isource()
        isource.num = 1
        isource.node = {Isource.I_TOP: '2', Isource.I_BOTTOM: '3'}
        isource.param = '0.5'
        isource.print_element()
        isource.print_node()

        isource2 = Isource(2, {Isource.I_TOP: '4', Isource.I_BOTTOM: '5'}, '0.5')
        isource2.print_element()
        isource2.print_node()

        print(f"TestIsource.get_element_str: [{isource2.get_element_str()}]")
        print(f"TestIsource.get_node_str: [{isource2.get_node_str()}]")


class TestMosfet(TestCase):
    def test_print_element(self):
        mosfet = Mosfet()
        mosfet.num = 1
        mosfet.node[Mosfet.M_DRAIN] = 'nd'
        mosfet.node[Mosfet.M_GATE] = 'ng'
        mosfet.node[Mosfet.M_SOURCE] = 'ns'
        mosfet.node[Mosfet.M_BULK] = 'nb'
        mosfet.model = 'cmosn'
        mosfet.length = 1.2e+7
        mosfet.width = 1.0e-6
        mosfet.multiple = Decimal('2.0')  # OK
        # mosfet.multiple = 2.0  # OK
        # mosfet.multiple = 'aaa'  # NG

        mosfet.print_element()
        mosfet.print_node()

        node = {Mosfet.M_DRAIN: 'nd', Mosfet.M_GATE: 'ng', Mosfet.M_SOURCE: 'ns', Mosfet.M_BULK: 'nb'}
        model = 'cmosn'
        length = 1.2e-7
        width = 1.0e-6
        multiple = 2.0
        mosfet2 = Mosfet(2, node, None, model, length, width, multiple)
        mosfet2.print_element()
        mosfet2.print_node()

        mosfet2.multiple = Decimal('-100.0')
        mosfet2.print_element()
        mosfet2.print_node()

        mosfet2.multiple = -200.0
        mosfet2.print_element()
        mosfet2.print_node()

        print(f"TestMosfet.get_element_str: [{mosfet2.get_element_str()}]")
        print(f"TestMosfet.get_node_str: [{mosfet2.get_node_str()}]")


class TestDiode(TestCase):
    def test_print_element(self):
        diode = Diode()
        diode.num = 1
        diode.node[Diode.D_TOP] = '2'
        diode.node[Diode.D_BOTTOM] = '3'
        diode.model = 'diode1'
        diode.area = 1.0
        diode.multiple = 2.0

        diode.print_element()
        diode.print_node()
        print(f"TestDiode.get_element_str: [{diode.get_element_str()}]")
        print(f"TestDiode.get_node_str: [{diode.get_node_str()}]")


class TestCccs(TestCase):
    def test_print_element(self):
        cccs = Cccs()
        cccs.num = 1
        cccs.node[Cccs.F_OUT_P] = '2'
        cccs.node[Cccs.F_OUT_M] = '3'
        cccs.vs_name = 'vsens'
        cccs.c_gain = '5.0'
        cccs.multiple = 2.0

        cccs.print_element()
        cccs.print_node()

        print(f"TestCccs.get_element_str: [{cccs.get_element_str()}]")
        print(f"TestCccs.get_node_str: [{cccs.get_node_str()}]")


class TestCcvs(TestCase):
    def test_print_element(self):
        ccvs = Ccvs()
        ccvs.num = 1
        ccvs.node[Ccvs.H_OUT_P] = '2'
        ccvs.node[Ccvs.H_OUT_M] = '3'
        ccvs.vs_name = "vsens"
        ccvs.transresistance = "0.5k"

        ccvs.print_element()
        ccvs.print_node()

        print(f"TestCcvs.get_element_str: [{ccvs.get_element_str()}]")
        print(f"TestCcvs.get_node_str: [{ccvs.get_node_str()}]")


class TestVccs(TestCase):
    def test_print_element(self):
        vccs = Vccs()
        vccs.num = 1
        vccs.node[Vccs.G_OUT_P] = '2'
        vccs.node[Vccs.G_OUT_M] = '3'
        vccs.node[Vccs.G_IN_P] = '4'
        vccs.node[Vccs.G_IN_M] = '5'
        vccs.transconductance = 0.1
        vccs.multiple = 3.0

        vccs.print_element()
        vccs.print_node()

        print(f"TestVccs.get_element_str: [{vccs.get_element_str()}]")
        print(f"TestVccs.get_node_str: [{vccs.get_node_str()}]")


class TestVcvs(TestCase):
    def test_print_element(self):
        vcvs = Vcvs()
        vcvs.num = 1
        vcvs.node[Vcvs.E_OUT_P] = '2'
        vcvs.node[Vcvs.E_OUT_M] = '3'
        vcvs.node[Vcvs.E_IN_P] = '4'
        vcvs.node[Vcvs.E_IN_M] = '5'
        vcvs.v_gain = -1.0

        vcvs.print_element()
        vcvs.print_node()

        print(f"TestVcvs.get_element_str: [{vcvs.get_element_str()}]")
        print(f"TestVcvs.get_node_str: [{vcvs.get_node_str()}]")


class TestCircuit(TestCase):

    def test_print_element_list(self):
        self.fail()

    def test_make_circuit(self):
        vccs = Vccs()
        vccs.num = 1
        vccs.node[Vccs.G_OUT_P] = '2'
        vccs.node[Vccs.G_OUT_M] = '3'
        vccs.node[Vccs.G_IN_P] = '4'
        vccs.node[Vccs.G_IN_M] = '5'
        vccs.transconductance = 0.1
        vccs.multiple = 3.0

        mosfet = Mosfet()
        mosfet.num = 1
        mosfet.node[Mosfet.M_DRAIN] = 'nd'
        mosfet.node[Mosfet.M_GATE] = 'ng'
        mosfet.node[Mosfet.M_SOURCE] = 'ns'
        mosfet.node[Mosfet.M_BULK] = 'nb'
        mosfet.model = 'cmosn'
        mosfet.length = 1.2e+7
        mosfet.width = 1.0e-6
        mosfet.multiple = Decimal('2.0')  # OK

        vsource = Vsource()
        vsource.num = 'dd'
        vsource.node = {Vsource.V_TOP: '2', Vsource.V_BOTTOM: '3'}
        vsource.param = "dc 1.5 ac 1"

        circuit = Circuit()
        circuit.make_circuit([vccs, mosfet, vsource])
        circuit.print_elements()

        print(circuit.size())

    def test_read_circuit(self):
        circuit = Circuit()
        circuit.read_circuit('../Sp_Data/OPamp_new.sp')
        print(f"size={circuit.size()}")
        circuit.print_elements()
        print(f"circuit.count={circuit.count}")
        print(f"circuit.node_info={circuit.node_info()}")
        print(f"circuit.node_list={circuit.node_list}")
        print(f"circuit.power_supply={circuit.power_supply}")

    def test_write_circuit(self):
        circuit = Circuit()
        circuit.read_circuit('../Sp_Data/OPamp_new.sp')
        circuit.write_circuit('OPamp_OUT2.sp')

    def test_node_info(self):
        circuit = Circuit()
        circuit.read_circuit('../Sp_Data/OPamp_new.sp')
        circuit.node_info()
