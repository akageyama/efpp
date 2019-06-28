!!>
!  sample for efpp, ver.180831
!!<
program main
  use constants_m
  use time_m
  use vecfield_m
  implicit none

  type(time__t) :: time = time__t(0, 0.1_DR, 0.0_DR)
  logical :: just_once = .true.

  type(vecfield__t) :: magnetic
  real(DR) :: energy, dvol2 = GRID_DVOL/2

  print *, "\\main(16): ", " dvol2 = ", dvol2
  print *, "\\main(17): ", "kind vals:", " SI = ", SI, " DI = ", DI, " SR = ", SR, " DR = ", DR

  do while ( time%loop <= 10 )
    !!><just_once>==
      ! this part is called only once.
      call vecfield__init(magnetic)
    !!<</just_once>==

     !!>
!         Normalized magnetic energy
!           = \int_V \frac{B^2}{2} dV
     !!<
    energy = sum(magnetic .dot. magnetic) * dvol2

    magnetic%x(:,:,:) = magnetic%x(:,:,:) * 0.70710678118654752_DR

    time%loop = time%loop + 1
    time%t = time%t + time%dt  ;print *, "\\main(34): ", " time.loop = ", time%loop, " time.t = ", time%t, " energy = ", energy
  end do

  print *, "\\main(37): ", " time.loop = ", time%loop, " time.t = ", time%t

  print *, "\\main(39): ", " magnetic.x(1, 1, 1) = ", magnetic%x(1, 1, 1)

  if ( vecfield__is_zero_BOOLEAN(magnetic) )  print *, "zero?!"

end program main
