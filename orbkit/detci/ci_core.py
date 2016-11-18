from . import cy_ci
from ..analytical_integrals import get_nuclear_dipole_moment
from ..display import display
from .. import omp_functions
import numpy

def mu(cia,cib,qc,zero,sing,omr,omv):
  '''Computes the analytic transition dipole moments in length and velocity gauge.
  '''
  mur,muv = cy_ci.get_mu(zero,sing,omr,omv) 

  for component in range(3):
    if cia == cib:
      mur[component] = -mur[component] + get_nuclear_dipole_moment(qc,component=component)
    else:
      mur[component] = -mur[component]
  
  muv *= -1.0
  delta_v = float(cib.info['energy'])-float(cia.info['energy'])
  mur_v = numpy.zeros((3,))
  if delta_v != 0.0:
    mur_v = muv/delta_v
  
  return mur, muv, mur_v


def enum(zero,sing,moom):
  '''Computes the norm of the wavefunction using analytical integrals.
  '''
  return cy_ci.get_enum(zero,sing,moom)


def slice_rho(ij):  
  '''Computes the electron (transition) density on a grid for a single slice.
  '''
  return cy_ci.get_rho(ij[0],ij[1],multici['zero'],multici['sing'],multici['molist'])


def rho(zero,sing,molist,slice_length=1e4,numproc=1):
  '''Computes the electron (transition) density on a grid.
  '''
  global multici
  multici = {'zero': zero, 'sing': sing, 'molist':molist}
  
  slice_length = min(molist.shape[1],slice_length)
  ij = numpy.arange(0,molist.shape[1]+1,abs(int(slice_length)),dtype=numpy.intc)
  ij = zip(ij[:-1],ij[1:])
  
  data = numpy.zeros(molist.shape[1])
  return_val = omp_functions.run(slice_rho,x=ij,numproc=min(len(ij),numproc),display=display)
  for k,(i,j) in enumerate(ij):
    data[i:j] = return_val[k]
  
  return data

def slice_jab(ij):   
  '''Computes the electronic (transition) flux density on a grid for a single slice.
  '''  
  return cy_ci.get_jab(ij[0],ij[1],multici['zero'],multici['sing'],multici['molist'],multici['molistdrv'])


def jab(zero,sing,molist,molistdrv,slice_length=1e4,numproc=1):
  '''Computes the electronic (transition) flux density on a grid.
  '''  
  global multici
  multici = {'zero': zero, 'sing': sing, 'molist':molist, 'molistdrv':molistdrv}
    
  slice_length = min(molist.shape[1],slice_length)
  ij = numpy.arange(0,molist.shape[1]+1,abs(int(slice_length)),dtype=numpy.intc)
  ij = zip(ij[:-1],ij[1:])
  
  data = numpy.zeros((3,molist.shape[1]))
  return_val = omp_functions.run(slice_jab,x=ij,numproc=min(len(ij),numproc),display=display)
  for k,(i,j) in enumerate(ij):
    data[:,i:j] = return_val[k]

  return data

def slice_a_nabla_b(ij):  
  
  return cy_ci.get_a_nabla_b(ij[0],ij[1],multici['zero'],multici['sing'],multici['molist'],multici['molistdrv'])


def a_nabla_b(zero,sing,molist,molistdrv,slice_length=1e4,numproc=1):
  
  global multici
  multici = {'zero': zero, 'sing': sing, 'molist':molist, 'molistdrv':molistdrv}
    
  slice_length = min(molist.shape[1],slice_length)
  ij = numpy.arange(0,molist.shape[1]+1,abs(int(slice_length)),dtype=numpy.intc)
  ij = zip(ij[:-1],ij[1:])
  
  data = numpy.zeros((3,molist.shape[1]))
  return_val = omp_functions.run(slice_a_nabla_b,x=ij,numproc=min(len(ij),numproc),display=display)
  for k,(i,j) in enumerate(ij):
    data[:,i:j] = return_val[k]

  return data