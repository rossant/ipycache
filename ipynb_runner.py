"""
Script for running ipython notebooks.
"""
from __future__ import print_function
from IPython.nbformat.current import read
from IPython.kernel import KernelManager
import argparse
#from pprint import pprint
import sys

def get_ncells(nb):
    # return number of code cells in a notebook
    ncells=0
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type=="code":
                ncells+=1
    return ncells
        
# input arguments parsing
parser = argparse.ArgumentParser(description="Run an IPython Notebook")
parser.add_argument("notebook", 
                    type=str, 
                    help='notebook to run')
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-b", "--break-at-error", help="stop at error",
                    action="store_true")
parser.add_argument("-s", "--summary", help="print summary",
                    action="store_true")

args = parser.parse_args()

# add .ipynb extension if not given
notebook = '{name}{ext}'.format(name=args.notebook, ext=''
                                if '.' in args.notebook else '.ipynb')

if args.verbose:
    print('Checking: {}'.format(notebook))

nb = read(open(notebook), 'json')

# starting up kernel
km = KernelManager()
km.start_kernel()
kc = km.client()
kc.start_channels()
kc.wait_for_ready()
shell=kc.shell_channel

ncells=get_ncells(nb)

nerrors=0 # accumulate number of errors
nsucc=0

# loop over cells
icell=1
for ws in nb.worksheets:
    for cell in ws.cells:
        if cell.cell_type == 'code':
            if args.verbose:
                print("Cell:%i/%i> "%(icell,ncells), end=" ")
            icell+=1
            kc.execute(cell.input)
            msg=kc.get_shell_msg()
            status=msg['content']['status']            
            if args.verbose:
                print( status )
            if status=='ok':
                nsucc+=1
                continue
            nerrors+=1
            if args.verbose:
                print( "="*80 )
                print( msg['content']['ename'], ":", msg['content']['evalue'] )
                print( "{0:-^80}".format("<CODE>") )
                print( cell.input )
                print( "{0:-^80}".format("</CODE>") )
                for m in msg['content']['traceback']:
                    print( m )
                print( "="*80 )
            if args.break_at_error:
                break
            
if args.summary:
    print( "{0:#^80}".format(" Summary: %s "%args.notebook) )
    print( "Num Errors   : ", nerrors )
    print(  "Num Successes: ", nsucc )
    print( "Num Cells    :  ", ncells )
    
            
# kernel cleanup
kc.stop_channels()
km.shutdown_kernel(now=True)
sys.exit(-1 if nerrors>0 else 0)
