import logging as log

from virttest import test_setup
from virttest.staging import utils_memory
from virttest.libvirt_xml import capability_xml

from provider.numa import numa_base


# Using as lower capital is not the best way to do, but this is just a
# workaround to avoid changing the entire file.
logging = log.getLogger('avocado.' + __name__)


def setup_default(test_obj):
    """
    Default setup function for the test

    :param test_obj: NumaTest object
    """
    hpc = test_setup.HugePageConfig(test_obj.params)
    all_nodes = test_obj.online_nodes_withmem
    hpc.set_node_num_huge_pages(1, all_nodes[0], 16777216)
    allocated_num = hpc.get_node_num_huge_pages(all_nodes[0], 16777216)
    if allocated_num < 1:
        test_obj.test.cancel("Can not set at least one page with pagesize 16777216 on "
                              "node '%s'" % all_nodes[0])


def run_default(test_obj):
    """
    Default run function for the test

    :param test_obj: NumaTest object
    """
    capa_xml = capability_xml.CapabilityXML()
    topo_xml = capa_xml.cells_topology
    cells = topo_xml.get_cell(withmem=True)
    pages_list = cells[0].pages
    total_mem = utils_memory.memtotal(node_id=cells[0].cell_id)
    for one_page in pages_list:
        page_size = int(one_page.fetch_attrs()['size'])
        if page_size == 64:
            page_num_64k = int(one_page.fetch_attrs()['pages'])
        if page_size == 16777216:
            hugepage_num_16g = int(one_page.fetch_attrs()['pages'])
    if total_mem != page_num_64k * 64 + hugepage_num_16g * 16777216:
        test_obj.test.fail("The sum memory of defaultpage and 16G hugepage is not"
                           " equal to the total memory")


def teardown_default(test_obj):
    """
    Default teardown function for the test

    :param test_obj: NumaTest object
    """
    test_obj.teardown()

    hpc = test_setup.HugePageConfig(test_obj.params)
    hpc.set_kernel_hugepages(16777216, 0)

    test_obj.test.log.debug("Step: teardown is done")


def run(test, params, env):
    """
    Test the command virsh capabilities

    (1) Allocate a 16G hugepage memory on numa node 0
    (2) Call virsh capabilities
    (3) Check if the memory page calculating correct on numa node 0
    """

    """
    Test for numa memory binding with emulator thread pin
    """
    vm_name = params.get("main_vm")
    vm = env.get_vm(vm_name)
    numatest_obj = numa_base.NumaTest(vm, params, test)
    try:
        setup_default(numatest_obj)
        run_default(numatest_obj)
    finally:
        teardown_default(numatest_obj)