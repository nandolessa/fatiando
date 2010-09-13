"""
Perform a tomography on synthetic travel time data using Total Variation
regularization for sharpness.
"""

import logging

# Configure the logging output to print to stderr
baselog = logging.getLogger()
stderrhandle = logging.StreamHandler()
stderrhandle.setFormatter(logging.Formatter())
baselog.addHandler(stderrhandle)
baselog.setLevel(logging.DEBUG)

# Make a logger for the script
log = logging.getLogger('script')
log.setLevel(logging.DEBUG)

import pylab
import numpy

from fatiando.seismo import synthetic, io
from fatiando.inversion import simpletom    
import fatiando.geometry                            
import fatiando.utils
import fatiando.stats
from fatiando.visualization import residuals_histogram, \
                                   plot_square_mesh   

# Load the synthetic model for comparison
model = synthetic.vel_from_image('model.jpg', vmax=5, vmin=1)

# Load the travel time data
data = io.load_traveltime('traveltimedata.txt')

error = data['error'][0]

# Make the model space mesh
model_ny, model_nx = model.shape

mesh = fatiando.geometry.square_mesh(x1=0, x2=model_nx, y1=0, y2=model_ny, 
                                     nx=model_nx, ny=model_ny)

# Inversion parameters
initial = numpy.ones(mesh.size)
damping = 10**(-7)
smoothness = 0
curvature = 0
sharpness = 3*10**(-1)
beta = 10**(-4)

# Solve
estimate, goals = simpletom.solve(data, mesh, initial, damping, smoothness, 
                                  curvature, sharpness, beta, 
                                  lm_start=1)

# Put the result in the mesh (for plotting)
simpletom.fill_mesh(estimate, mesh)

# Calculate the residuals
residuals = simpletom.residuals(data, estimate)

# Contaminate the data with Gaussian noise and re-run the inversion to estimate
# the error 
estimates = [estimate]
contam_times = 5

log.info("Contaminating data with %g error and re-running %d times" 
         % (error, contam_times))

for i in xrange(contam_times):
    
    cont_data = data.copy()
    
    cont_data['traveltime'] = fatiando.utils.contaminate(data['traveltime'], 
                                                         stddev=error, 
                                                         percent=False, 
                                                         return_stddev=False)
    
    new_estimate, new_goal = simpletom.solve(cont_data, mesh, initial, damping, 
                                             smoothness, curvature, sharpness, 
                                             beta, lm_start=1)
    
    estimates.append(new_estimate)
        
# Calculate the standard deviation of the estimates
stddev_estimate = fatiando.stats.stddev(estimates)
std_mesh = fatiando.geometry.copy_mesh(mesh)
simpletom.fill_mesh(stddev_estimate, std_mesh)

# Plot the synthetic model and inversion results
pylab.figure(figsize=(12,8))
pylab.suptitle("X-ray simulation: Sharp tomography", fontsize=14)

vmin = min(estimate.min(), model.min())
vmax = max(estimate.max(), model.max())

pylab.subplot(2,2,1)
pylab.axis('scaled')
pylab.title("Synthetic velocity model")
ax = pylab.pcolor(model, cmap=pylab.cm.jet, vmin=vmin, vmax=vmax)
cb = pylab.colorbar()
cb.set_label("Velocity")
pylab.xlim(0, model.shape[1])
pylab.ylim(0, model.shape[0])

pylab.subplot(2,2,2)
pylab.axis('scaled')
pylab.title("Inversion result")
plot_square_mesh(mesh, vmin=vmin, vmax=vmax)
cb = pylab.colorbar()
cb.set_label("Velocity")
pylab.xlim(0, model.shape[1])
pylab.ylim(0, model.shape[0])

pylab.subplot(2,2,3)
pylab.axis('scaled')
pylab.title("Result Standard Deviation")
plot_square_mesh(std_mesh)
pylab.colorbar()
pylab.xlim(0, model.shape[1])
pylab.ylim(0, model.shape[0])

pylab.subplot(2,2,4)
pylab.title("Histogram of residuals")
residuals_histogram(residuals, nbins=len(residuals)/10)
pylab.xlabel("Residual travel time")
pylab.ylabel("Residual count")

pylab.show()