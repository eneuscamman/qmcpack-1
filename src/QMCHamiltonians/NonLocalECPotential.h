//////////////////////////////////////////////////////////////////////////////////////
// This file is distributed under the University of Illinois/NCSA Open Source License.
// See LICENSE file in top directory for details.
//
// Copyright (c) 2016 Jeongnim Kim and QMCPACK developers.
//
// File developed by: Ken Esler, kpesler@gmail.com, University of Illinois at Urbana-Champaign
//                    Jeremy McMinnis, jmcminis@gmail.com, University of Illinois at Urbana-Champaign
//                    Jeongnim Kim, jeongnim.kim@gmail.com, University of Illinois at Urbana-Champaign
//                    Jaron T. Krogel, krogeljt@ornl.gov, Oak Ridge National Laboratory
//                    Mark A. Berrill, berrillma@ornl.gov, Oak Ridge National Laboratory
//
// File created by: Jeongnim Kim, jeongnim.kim@gmail.com, University of Illinois at Urbana-Champaign
//////////////////////////////////////////////////////////////////////////////////////
    
    
#ifndef QMCPLUSPLUS_NONLOCAL_ECPOTENTIAL_H
#define QMCPLUSPLUS_NONLOCAL_ECPOTENTIAL_H
#include "QMCHamiltonians/NonLocalTOperator.h"
#include "QMCHamiltonians/NonLocalECPComponent.h"
#include "QMCHamiltonians/ForceBase.h"

namespace qmcplusplus
{

/** @ingroup hamiltonian
 * \brief Evaluate the semi local potentials
 */
class NonLocalECPotential: public QMCHamiltonianBase, public ForceBase
{
  public:
  ///number of ions
  int NumIons;
  ///index of distance table for the ion-el pair
  int myTableIndex;
  ///the set of local-potentials (one for each ion)
  std::vector<NonLocalECPComponent*> PP;
  ///unique NonLocalECPComponent to remove
  std::vector<NonLocalECPComponent*> PPset;
  ///reference to the center ion
  ParticleSet& IonConfig;
  ///reference to the electrons
  ParticleSet& Peln;
  ///target TrialWaveFunction
  TrialWaveFunction& Psi;
  ///use T-moves
  int UseTMove;
  ///non local operator
  NonLocalTOperator nonLocalOps;
  ///random number generator
  RandomGenerator_t* myRNG;
  ///true if we should compute forces
  bool ComputeForces;
  ///true if we should use new algorithm
  bool UseVP;
  ParticleSet::ParticlePos_t PulayTerm;
#if !defined(REMOVE_TRACEMANAGER)
  ///single particle trace samples
  Array<TraceReal,1>* Ve_sample;
  Array<TraceReal,1>* Vi_sample;
#endif

  NonLocalECPotential(ParticleSet& ions, ParticleSet& els,
                      TrialWaveFunction& psi, bool computeForces=false, bool useVP=false);

  ~NonLocalECPotential();

  void resetTargetParticleSet(ParticleSet& P);

#if !defined(REMOVE_TRACEMANAGER)
  virtual void contribute_particle_quantities();
  virtual void checkout_particle_quantities(TraceManager& tm);
  virtual void delete_particle_quantities();
#endif

  Return_t evaluate(ParticleSet& P);

  Return_t evaluateWithToperator(ParticleSet& P);

  /** compute the T move transition probability for a given electron
   * @param P particle set
   * @param ref_elec reference electron id
   * @param Txy a vector of transition probability
   */
  void computeOneElectronTxy(ParticleSet& P, const int ref_elec, std::vector<NonLocalData>& Txy);

  /** set non local moves options
   * @param cur the xml input
   */
  void setNonLocalMoves(xmlNodePtr cur) { UseTMove = nonLocalOps.put(cur); }

  /** make non local moves with particle-by-particle moves
   * @param P particle set
   * @return the number of accepted moves
   */
  int makeNonLocalMovesPbyP(ParticleSet& P);

  /** make non local moves with all-particle moves
   * @param P particle set
   * @return the number of accepted moves
   */
  int makeNonLocalMovesAll(ParticleSet& P){ return 0; }

  Return_t evaluateValueAndDerivatives(ParticleSet& P,
      const opt_variables_type& optvars,
      const std::vector<RealType>& dlogpsi,
      std::vector<RealType>& dhpsioverpsi);

  /** Do nothing */
  bool put(xmlNodePtr cur)
  {
    return true;
  }

  bool get(std::ostream& os) const
  {
    os << "NonLocalECPotential: " << IonConfig.getName();
    return true;
  }

  QMCHamiltonianBase* makeClone(ParticleSet& qp, TrialWaveFunction& psi);

  void add(int groupID, NonLocalECPComponent* pp);

  void setRandomGenerator(RandomGenerator_t* rng) { myRNG = rng; }

  void addObservables(PropertySetType& plist, BufferType& collectables);

  void setObservables(PropertySetType& plist);

  void setParticlePropertyList(PropertySetType& plist, int offset);

  void registerObservables(std::vector<observable_helper*>& h5list,
                           hid_t gid) const;

  private:
  void evaluate(ParticleSet& P, bool Tmove, std::vector<NonLocalData>& Txy);
};
}
#endif


