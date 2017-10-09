import numpy
from . import AOIntegrals, FCIDUMP
from . import symmetry
from itertools import chain

def generate_fcidump(qc, filename='FCIDUMP', core=0, occ=None, sym='c1', ordering='molpro', max_dims=0):
  '''Creates a FCIDUMP file from a QCInfo object.

    **Parameters:**

      filename : string
      core, occ : int or list of ints
        active space (core and occupied) orbitals per IRREP
      sym : string ('d2h', 'c2v', 'c2h', 'd2', 'cs', 'c2', 'ci', 'c1')
        Do not exploit symmetry.
      ordering : 'molpro' or 'cotton'
        IRREP ordering in FCIDUMP file
      max_dims : int
        If > 0, calculate AO Integrals in slices containing no more than max_dims AOs (but at least one shell). Slower, but requires less memory.
  '''

  sym = sym.lower()

  assert sym in symmetry.point_groups
  ao = AOIntegrals(qc)

  if sym == 'c1':

    if occ is None:
      occ = ao.Norb
    nmopi = [ao.Norb]
    MOranges = [range(occ)]

  else:

    # get MOs of each IRREP
    MOs = [[] for i in range(symmetry.Nirreps[sym])]
    for imo, mo in enumerate(qc.mo_spec):
      irrep = mo['sym'].split('.')[1]
      MOs[symmetry.parse_irrep(irrep, sym)-1].append(imo)

    if ordering == 'cotton':
      # switch ordering
      MOs = [MOs[symmetry.cotton2molpro[sym].index(i+1)-1] for i in range(symmetry.Nirreps[sym])]

    # group MOs by IRREPs
    order = list(chain(*MOs))
    coeffs = qc.mo_spec.coeffs[order,:]
    qc.mo_spec.set_coeffs(coeffs)
    nmopi = [len(m) for m in MOs]

    # create blocks of MOs by IRREP
    MOranges = [0]
    MOranges.extend(numpy.cumsum(nmopi))
    MOranges = [range(MOranges[i], MOranges[i+1]) for i in range(len(nmopi))]

    if occ is None:
      occ = nmopi
    elif isinstance(occ, int):
      occ = [occ]

  # create FCIDUMP instance
  if isinstance(occ, int):
    Norb = occ
  else:
    Norb = sum(occ)

  fcidump = FCIDUMP(Norb=Norb, Nelec=qc.get_elec_charge(), spin=1)
  fcidump.set_OrbSym(nmopi)
  fcidump.nuclear_repulsion = qc.nuclear_repulsion

  # calculate Hcore
  for ii, MOrange in enumerate(MOranges):
    ao.add_MO_block_1e(MOrange, MOrange)

  blocks = ao.Hcore(asMO=1, max_dims=max_dims)

  if len(MOranges) == 1:
    fcidump.H = blocks
  else:
    for ii, block in enumerate(blocks):
      fcidump.set_H(block, irrep=ii+1)

  # calculate ERI
  ind = []
  for i in range(len(nmopi)):
    for j in range(i, len(nmopi)):       # hermitian
      for k in range(i, len(nmopi)):     # exchange of electronic coordinates
        for l in range(k, len(nmopi)):   # hermitian

          _i, _j, _k, _l = i+1, j+1, k+1, l+1
          if symmetry.irrep_mul(_i, _j, _k, _l) != 1:
            continue

          ao.add_MO_block_2e(
            MOrangei=MOranges[i],
            MOrangej=MOranges[j],
            MOrangek=MOranges[k],
            MOrangel=MOranges[l],
          )
          ind.append((_i, _j, _k, _l))

  blocks = ao.Vee(asMO=1, max_dims=max_dims)

  if len(MOranges) == 1:
    fcidump.G = blocks
  else:
    for i, block in enumerate(blocks):
      i, j, k, l = ind[i]
      fcidump.set_G(block, i, j, k, l)

  # incorporate core orbitals
  fcidump.reduce_active_space(core=core)

  # write to file
  if filename:
    fcidump.store(filename)

  return fcidump
