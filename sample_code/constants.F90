!!>
!    !!>
!!
!!  sample for efpp, ver.180831
!!
!    !!<
!!<
!*********************************************************
module constants_m
!*********************************************************
  implicit none

  !<< f90 constants >>!
  integer, parameter :: SI = selected_int_kind(6)
  integer, parameter :: DI = selected_int_kind(15)
  integer, parameter :: SR = selected_real_kind(6)
  integer, parameter :: DR = selected_real_kind(15)

  !<< Mathematical constants >>!
  real(DR), parameter :: PI = 3.141592653589793_DR
  real(DR), parameter :: TWOPI = PI*2

  !<< Simulation constants >>!
  integer(SI), parameter :: GRID_NX = 10
  integer(SI), parameter :: GRID_NY = 12
  integer(SI), parameter :: GRID_NZ = 14
  real(DR), parameter :: GRID_DX = 1.0_DR / GRID_NX
  real(DR), parameter :: GRID_DY = 1.0_DR / GRID_NY
  real(DR), parameter :: GRID_DZ = 1.0_DR / GRID_NZ
  real(DR), parameter :: GRID_DVOL = GRID_DX*GRID_DY*GRID_DZ

end module constants_m
