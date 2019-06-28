!!>
!  sample for efpp, ver.180831
!!<
!*********************************************************
module vecfield_m
!*********************************************************
  use constants_m
  implicit none

  private
  public :: operator( .dot. ),  &
            vecfield__init,  &
            vecfield__is_zero_BOOLEAN

  type, public :: vecfield__t
    real(DR) :: x(GRID_NX,GRID_NY,GRID_NZ)
    real(DR) :: y(GRID_NX,GRID_NY,GRID_NZ)
    real(DR) :: z(GRID_NX,GRID_NY,GRID_NZ)
  end type vecfield__t

  interface operator( .dot. )
     module procedure operator_dot_product
  end interface


contains

!_________________________________________________private__
!
  function operator_dot_product(a,b)
    type(vecfield__t), intent(in) :: a, b
    real(DR), dimension(GRID_NX,  &
                        GRID_NY,  &
                        GRID_NZ) :: operator_dot_product
!__________________________________________________________
!
    operator_dot_product  = a%x*b%x
    operator_dot_product = operator_dot_product + a%y*b%y
    operator_dot_product = operator_dot_product + a%z*b%z

  end function operator_dot_product


!_________________________________________________public___
!
  subroutine vecfield__init(a)
    type(vecfield__t), intent(out) :: a
!__________________________________________________________
!
    print *, "\\vecfield_m(50): ", ' hello. I am in a function named vecfield__init'
    print *, "\\vecfield_m(51): ", '        which is in vecfield_m'
    print *, "\\vecfield_m(52): ", '        this is at line number 52'
    print *, "\\vecfield_m(53): ", '        in short, ', 'i am in vecfield_m/vecfield__init'

    a%x(:,:,:) = 1.0_DR
    a%y(:,:,:) = 0.0_DR
    a%z(:,:,:) = 0.0_DR

  end subroutine vecfield__init


!_________________________________________________public___
!
  function vecfield__is_zero_BOOLEAN(a) result(ans)
    type(vecfield__t), intent(in) :: a
    logical :: ans
!__________________________________________________________
!
    print *, "\\vecfield_m(69): ", ' hello. I am in a function named vecfield__is_zero_BOOLEAN'
    print *, "\\vecfield_m(70): ", '        which is in vecfield_m'
    print *, "\\vecfield_m(71): ", '        this is at line number 71'
    print *, "\\vecfield_m(72): ", '        in short, ', 'i am in vecfield_m/vecfield__is_zero_BOOLEAN'

    ans = ( sum( a .dot. a ) == 0.0_DR )

  end function vecfield__is_zero_BOOLEAN

end module vecfield_m
