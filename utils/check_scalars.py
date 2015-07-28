#!/usr/bin/env python

# Statical error checking code for use by testing framework
# Jaron Krogel/ORNL

import os
from optparse import OptionParser
from numpy import loadtxt,array,sqrt

# Returns failure error code to OS.
# Explicitly prints 'fail' after an optional message.
def exit_fail(msg=None):
    if msg!=None:
        print msg
    #end if
    print 'fail'
    exit(1)
#end def exit_fail


# Returns success error code to OS.
# Explicitly prints 'pass' after an optional message.
def exit_pass(msg=None):
    if msg!=None:
        print msg
    #end if
    print 'pass'
    exit(0)
#end def exit_pass


# Calculates the mean, variance, errorbar, and autocorrelation time
# for a 1-d array of statistical data values.
# If 'exclude' is provided, the first 'exclude' values will be 
# excluded from the analysis.
def simstats(x,exclude=None):
    if exclude!=None:
        x = x[exclude:]
    #end if

    N    = len(x)
    mean = x.mean()
    var  = x.var()

    i=0          
    tempC=0.5
    kappa=0.0
    if abs(var)<1e-15:
        kappa = 1.0
    else:
        ovar=1.0/var
        while (tempC>0 and i<(N-1)):
            kappa=kappa+2.0*tempC
            i=i+1
            tempC = ovar/(N-i)*((x[0:N-i]-mean)*(x[i:N]-mean)).sum()
        #end while
        if kappa == 0.0:
            kappa = 1.0
        #end if
    #end if
    Neff=(N+0.0)/(kappa+0.0)
    if (Neff == 0.0):
        Neff = 1.0
    #end if
    error=sqrt(var/Neff)

    return (mean,var,error,kappa)
#end def simstats



# Reads command line options.
# For example:
#   check_scalars.py  --ns 2  -p Li  -s '1 3' -e 10  --le '-7.478011 0.000035  -7.478059 0.000035'
# This invocation expects two scalar files to be present:
#   Li.s001.scalar.dat  Li.s003.scalar.dat
# The local energy ('le') will be computed excluding ('e') 10 blocks each.
# the test passes if both of the following are true:
#   |local_energy_mean_of_series_1 - (-7.478011)| < 2*0.000035
#   |local_energy_mean_of_series_3 - (-7.478059)| < 2*0.000035
# Note that the factor of 2 is specified by 'ns', the allowed number of sigma deviations for the test.
# The inputted errorbar (sigma) to check against (0.000035) should satisfy the following:
#   Let err_ref be the error bar of the reference solution.
#   Let err_comp be the expected errorbar of the completed test run.
#   Then the provided errorbar/sigma should be sqrt( err_ref**2 + err_comp**2 ).
def read_command_line():
    try:

        parser = OptionParser(
            usage='usage: %prog [options]',
            add_help_option=False,
            version='%prog 0.1'
            )

        parser.add_option('-h','--help',dest='help',
                          action='store_true',default=False,
                          help='Print help information and exit (default=%default).'
                          )
        parser.add_option('-p','--prefix',dest='prefix',
                          default='qmc',
                          help='Prefix for output files (default=%default).'
                          )
        parser.add_option('-s','--series',dest='series',
                          default='0',
                          help='Output series to analyze (default=%default).'
                          )
        parser.add_option('-e','--equilibration',dest='equilibration',
                          default='0',
                          help='Equilibration length in blocks (default=%default).'
                          )
        parser.add_option('-n','--nsigma',dest='nsigma',
                          default='3',
                          help='Sigma requirement for pass/fail (default=%default).'
                          )

        quantities = dict(
            ar   = 'AcceptRatio',
            le   = 'LocalEnergy',
            ke   = 'Kinetic',
            lp   = 'LocalPotential',
            ee   = 'ElecElec',
            cl   = 'Coulomb',
            ii   = 'IonIon',
            lpp  = 'LocalECP',
            nlpp = 'NonLocalECP',
            mpc  = 'MPC',
            kec  = 'KEcorr'
            )

        for qshort in sorted(quantities.keys()):
            qlong = quantities[qshort]
            parser.add_option('--'+qshort,'--'+qlong,dest=qlong,
                              default=None,
                              help='Reference value and errorbar for '+qlong+' (one value/error pair per series).'
                              )
        #end for

        options,files_in = parser.parse_args()

        if options.help:
            print '\n'+parser.format_help().strip()
            exit()
        #end if

        options.series         = array(options.series.split(),dtype=int)
        options.equilibration  = array(options.equilibration.split(),dtype=int)
        if len(options.series)>0 and len(options.equilibration)==1:
            options.equilibration = array(len(options.series)*[options.equilibration[0]],dtype=int)
        #end if
        options.nsigma         = float(options.nsigma)

        quants_check = []
        for q in quantities.values():
            v = options.__dict__[q]
            if v!=None:
                vref = array(v.split(),dtype=float)
                if len(vref)!=2*len(options.series):
                    exit_fail('must provide one reference value and errorbar for '+q)
                #end if
                options.__dict__[q] = vref
                quants_check.append(q)
            #end if
        #end for
    except Exception,e:
        exit_fail('error during command line read:\n'+str(e))
    #end try

    return options,quants_check
#end def read_command_line



# Reads scalar.dat files and performs statistical analysis.
def process_scalar_files(options,quants_check):
    values = dict()

    try:
        ns = 0
        for s in options.series:
            svals = dict()
            scalar_file = options.prefix+'.s'+str(int(s)).zfill(3)+'.scalar.dat'

            if os.path.exists(scalar_file):
                rawdata = loadtxt(scalar_file)[:,1:].transpose()

                fobj = open(scalar_file,'r')
                quantities = fobj.readline().split()[2:]
                fobj.close()

                equil = options.equilibration[ns]

                data  = dict()
                stats = dict()
                for i in range(len(quantities)):
                    q = quantities[i]
                    d = rawdata[i,:]
                    data[q]  = d
                    stats[q] = simstats(d,equil)
                #end for

                if 'LocalEnergy_sq' in data and 'LocalEnergy' in data:
                    v = data['LocalEnergy_sq'] - data['LocalEnergy']**2
                    stats['Variance'] = simstats(v,equil)
                #end if

                for q in quants_check:
                    if q in stats:
                        mean,var,error,kappa = stats[q]
                        svals[q] = mean,error
                    else:
                        exit_fail('{0} is not present in file {1}'.format(q,scalar_file))
                    #end if
                #end for
            else:
                exit_fail('scalar file does not exist: '+scalar_file)
            #end if

            values[s] = svals
            ns += 1
        #end for        
    except Exception,e:
        exit_fail('error during scalar file processing:\n'+str(e))
    #end try

    return values
#end def process_scalar_files


# Checks computed values from scalar.dat files 
# against specified reference values.
def check_values(options,quants_check,values):
    success = True

    try:
        ns = 0
        for s in options.series:
            for q in quants_check:
                ref = options.__dict__[q]
                mean_ref  = ref[2*ns]
                error_ref = ref[2*ns+1]
                mean_comp,error_comp = values[s][q]

                success &= abs(mean_comp-mean_ref) < options.nsigma*error_ref
            #end for
            ns+=1
        #end for
    except Exception,e:
        exit_fail('error during value check:\n'+str(e))
    #end try

    return success
#end def check_values



# Main execution
if __name__=='__main__':
    # Read and interpret command line options.
    options,quants_check = read_command_line()

    # Compute means of desired quantities from scalar.dat files.
    values = process_scalar_files(options,quants_check)

    # Check computed means agains reference solutions.
    success = check_values(options,quants_check,values)

    # Pass success/failure exit codes and strings to the OS.
    if success:
        exit_pass()
    else:
        exit_fail()
    #end if
#end if