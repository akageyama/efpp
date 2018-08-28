# efpp
efpp: A preprocessor for eFortran, a dialect of the modern Fortran


## Usage
efpp.py sample.e03 > sample.F90

Here sample.e03 is a eFortran program, and
sample.F90 is a standard Fortran 2003 program.

## Functions


### Member accessor by dot

You can access a member of a derived type by dot (.), instead of % in the standard Fortran.

```
 call field.advance(time.dt)
```

### Shorter declearations

For example, 

```
  inte(SI) <in> :: i, j, k
  real(DR) <optout> :: pi
```

### Subsdiary call

It is convenient for test or timer routine calls.

```
       xyz -call abc()  =>  xyz ;call abc()
           -call abc()  =>       call abc()
```

### "Just once" block

```
       program test
         logical :: just_once = .true.
         ==<just_once>==    ! you can put comment here.
           call subsub('asdfasdf')
         ==</just_once>==   ! end of just_once region.
       end program test
```

### "Skip" block

```
        # program test
        #   inte(SI) :: ctr=0
        #   inte(SI) :: i
        #   do i = 1 , 200
        #     ===<skip ctr:8>===  ! you can put comment.
        #       call subsub('asdfasdf',i)
        #     ===</skip ctr>===   ! end of skip block.
        #   end do
        # end program test
```

### Predefined macro

```
     __FUNC__   (is replaced by subprogram name)
     __MODULE__  (is replaced by module name)
     __LINE__  (is replaced by line number of the source code)
     __MODFUNC__  (is replaced by modulename followed by subprogram name)
```

### User-defined macro

You can define your own macro in a file named "efpp_alias.list". The alias strings are replaced acoording to the file in the following format

```
  "alias string"  => "replaced string"
```

An example of efpp_alias.list is

```
   "!debugp " => "print *, '\db\ __MODULE__(__LINE__): '//"

   "__EFPPVER__" => "180802"   
```


### Implicit none check

Check if implicit noe is called in each module.

### Operators

```
      "... val += aa" is converted to "... val = val + aa"

      "... val -= aa" is converted to "... val = val - aa"

      "... xyz *=  2" is converted to "... xyz = xyz * 2"

      but

       "val /= 2" is not converted (since it stands for val does not equal to 2).
```

### Block comment

```
      abc def ghijklmn opq
      =======
      abc def ghijklmn opq
        ======
        abc def ghijklmn opq
        abc def ghijklmn opq
        ======
      abc def ghijklmn opq
      =======
      abc def ghijklmn opq
```
becomes

```
     abc def ghijklmn opq
     !=======   
     !abc def ghijklmn opq
     !!  ====== 
     !!  abc def ghijklmn opq
     !!  abc def ghijklmn opq
     !!  ====== 
     !abc def ghijklmn opq
     !=======   
     abc def ghijklmn opq
```

## A tip to compile in Vim

The script efpp.py does not change the line numbers of the source code. One can make use of the quickfix feature of vim with minimum changes. when efpp.py sample.e03 > sample.F90 is applied, all we have to do is to change the source code name from sample.F90 into sample.e03. To automatically apply this, set the following map in your .vimrc:

```
nnoremap <silent> Y :copen<CR>:set modifiable<CR>:%s/.F90/.e03/<CR>:call histdel('/',-1)<CR>:cbuffer<CR>:cclose<CR>
```

(1) Type :make!

(2) Type Y


## Reference

S. Hosoyamada and A. Kageyama, A Dialect of Modern Fortran for Simulations, Proceedings of AsiaSim2018, Kyoto, Japan, 2018.
