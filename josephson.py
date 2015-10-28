#Regular calculation modules.
import numpy as np 
import scipy as sp 
#Allows a debug-output stream.
import sys as sys 
#Physical constants list.
from scipy.constants import *
#Time differences.
import time as time  
#Command line arguments.
import argparse as argparse 
#Plotting.
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt

#Commandline arguments instruction.
parser	= argparse.ArgumentParser(prog="Josephson.Py",
  description = "This file calculates the josephson current, given a microscopic mechanis, scattering mechanism and a resolution. Note that this file also has inspection modes.")  
parser.add_argument('-n', '--number', help='Resolution onf the calculation.', default = 10, action='store', type = int)  
parser.add_argument('-d', '--gapfunction', help='Resolution onf the calculation.', default = 10, action='store', type = int)  
parser.add_argument('-m', '--mechanism', help='Resolution onf the calculation.', default = 10, action='store', type = int)   
parser.add_argument('-p', '--plot', help='Resolution onf the calculation.', default = 10, action='store', type = int)  
parser.add_argument('-k', '--fermi', help='Fermi Surface.', default = 10, action='store', type = int)  
parser.add_argument('-b', '--band', help='Fermi Surface.', default = 10, action='store', type = int)  
parser.add_argument('-f', '--filename', help='Sets the filename. Only saves when given.', default = "default.png", action='store', type = str) 
parser.add_argument('-s', '--silent', help='Do not plot, do not save', default = False, action='store', type = bool) 
args	= parser.parse_args() 


N		= args.number 		#Resolution
gapfunction	= args.gapfunction 	#Gap function
mechanism	= args.mechanism 	#Scattering
plotMode	= args.plot 		#Plot Mode
filename	= args.filename 	#Filename if we want to save
fermi		= args.fermi 		#Type of Fermi surface
band		= args.band	 	#Band number. There are typically 4 bands as far as I can see.
silent		= args.silent	 	#Silent. Don't plot, don't save.

if N > 90:
	raise Exception("An initial test showed that, while for N<90 the program is well behaved and there is a definite linear scaling,\n N>90 leads to a sudden calculation time more than four times over N=90 which meant I cancelled it");

startTime = time.time();

if filename != "default.png":
	print "Saving Figure (%s) for -d %d -m %d -p %d -n %d." % (filename, gapfunction, mechanism, plotMode, N)
#Some physical constants.
hbar	=  physical_constants["Planck constant over 2 pi"][0]
mass	=  physical_constants["electron mass"][0]
ev	=  physical_constants["electron volt"][0]
lattice	= 3.787 * physical_constants["Angstrom star"][0] #(From Wikipedia)


eta	= hbar**2 / 2 / mass / ev / lattice**2
deltaS	= 3e-3
kFermi	= 3*np.pi/4
fluxnum = 2.0 
#small changes

dFlux = 4.0*fluxnum*np.pi/N
dDelta = 10*deltaS/N
dK = kFermi/N
dPhi = 2*np.pi/N

dkdphi = dK*dPhi;
#Make our arrays of parameters.
fluxArray	= np.arange(-fluxnum*2*np.pi,fluxnum*2*np.pi, dFlux)
deltaArray	= np.arange(2*deltaS/N, 10*deltaS, dDelta)
kArray		= np.arange(kFermi/N, kFermi, dK)
phiArray	= np.arange(0,2*np.pi, dPhi) 
#We define the figure here so that the different modes can assign labels/titles
fig = plt.figure(figsize=(15,15))
#Define Lambda functions.
Heaviside 	= lambda xx: 1.0 * (xx>0) 
Dirac 		= lambda xx: 1.0 * (xx==0) 
#Gap Function.
if gapfunction == 0: #d_{x^2-y^2}
	Delta	= lambda dd, kk, pp: dd * ( np.cos(kk*np.cos(pp)) - np.cos(kk*np.sin(pp)))
elif gapfunction == 1: #d_{xy}
	Delta = lambda dd, kk, pp: dd*np.sin(kk*np.cos(pp))*np.sin(kk*np.sin(pp))
elif gapfunction == 2: #s-wave
	Delta = lambda dd, kk, pp: dd
else:
	raise Exception("Unknown gap function.") 
#By far, the easiest way to incorporate the Fermi Surface is by just letting it tag along
#	with the tunnel functionality.
#	the only requirement is that the Fermi surface is at least as high as the maximum calculated length.
#	This requires us to calculate the fermi surface and, sadly, remake the kFermi, dK and kArray variables. 
#	It is, however, the smallest step.
if band >= 4:
	raise Exception("There are only four bands");

if fermi == 0:
	Fermi = lambda kk, pp: 1.0;
elif fermi == 1:
		
	from laosto import *
	from conductivity import *
	kF0 = [0.5*pi, 0.5*pi, 0.5*pi, 0.5*pi, -1, -1]
	system = LAOSTO(mu=0, H=30, theta=np.pi/4, g=5, gL=1, tl1=340, tl2=340, th=12.5, td=12.5, dE=60, dZ=15, dSO=5)
	
	
	kFermis, indices = kF_angle(system, phiArray, kF0)
	start = indices[band, 1]
	end = indices[band, 2]
	
	fermiLevel = kFermis[start:end,:]
	fermiSurface = ((fermiLevel**2).sum(axis=1))**0.5
	
	findFermi = lambda pp: fermiSurface[np.where(pp==phiArray)]
	
	Fermi = lambda kk,pp : 1.0
else:
	raise Exception("Unknown fermi surface requested.")

#The tunnel 'function' is required for the other functions.
if mechanism == 0: #constant rate
	tunnel = lambda kk, pp: 1.0 * Fermi(kk, pp)
elif mechanism == 1: #A slice of k-space.
	tunnel = lambda kk, pp: 1.0
else:
	raise Exception("Unknown tunnel function.") 
#Energies.
Energy		= lambda kk, dd: (eta*kk**2 + dd**2)**0.5
EnergyR		= lambda kk, dd, pp: (eta*kk**2 + Delta(kk,dd,pp)**2)**0.5
#Current
dCurrent	= lambda ff, dd, kk, pp:tunnel(kk,pp)*dkdphi*np.abs(Delta(dd, kk, pp))*deltaS*np.sin(np.angle(Delta(dd,kk,pp)) + ff) /( (Energy(kk,dd)+EnergyR(kk,dd,pp)) * (Energy(kk,dd)*EnergyR(kk,dd,pp)))
#Pre-plotting
ax = fig.add_subplot(111, projection='3d')  
ax.view_init(50, 80) 
#Mode switching 
title = "Unknown Mode." 
if plotMode == 0: #Plot tunnel function in k-space
	k, phi = np.meshgrid(kArray,phiArray)
	
	x = k * np.cos(phi)
	y = k * np.sin(phi)
	
	z = tunnel(x, y)
	
	plt.xlabel("k_x")
	plt.ylabel("k_y")
	title = "Tunneling Matrix";
elif plotMode == 1:  
	
	flux, delta, k, phi = np.meshgrid(fluxArray,deltaArray,kArray,phiArray);
	z = dCurrent(flux,delta, k, phi).sum(axis=-1).sum(axis=-1) 
	 
	
	x,y = np.meshgrid(fluxArray, deltaArray)
	
	plt.xlabel("Flux")
	plt.ylabel("Delta") 
	title = "Current";
elif plotMode == 2:  
	ax.view_init(0, 90) 
	#It's just mode 1 with a different view angle
	
	flux, delta, k, phi = np.meshgrid(fluxArray,deltaArray,kArray,phiArray);
	z = dCurrent(flux,delta, k, phi).sum(axis=-1).sum(axis=-1) 
	
	
	x,y = np.meshgrid(fluxArray, deltaArray) 
	
	plt.xlabel("Flux")
	plt.ylabel("Delta")   
	title = "Current_k_phi";
elif plotMode == 3:
	
	ax.view_init(30, 30) 
	k, phi = np.meshgrid(kArray,phiArray)
	
	x = k * np.cos(phi)
	y = k * np.sin(phi)
	
	z = Delta(1, k, phi);
	
	plt.xlabel("k_x")
	plt.ylabel("k_y")  
	title = "Gap function";
else:
	raise Exception("Unknown plot mode.");   
plt.title("%s, N=%d, d=%d, m=%d, p=%d, k=%d, b=%d" % (title, N,gapfunction, mechanism, plotMode, fermi, band))
ax.plot_surface(x, y, z, rstride=1, cstride=1, cmap=cm.summer,linewidth=0, antialiased=False) 

if silent:
	print "Silent Mode; no plotting, no saving.";
	plt.close();
if filename != "default.png":	
	fig.savefig(filename)
else:
	plt.show()
	
print "Elapsed time %2.3f" % (time.time() - startTime)