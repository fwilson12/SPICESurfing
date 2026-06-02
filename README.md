# SPICESurfing
**Setup** 
I reccomend creating a new environment in anaconda to install the dependencies 

```
conda create -n SPICE python=3.11
conda activate SPICE

pip install -r requirements.txt
```

Additionally, PySpice requires a local installation of ngspice, which you can install with this command
```
pyspice-post-installation --install-ngspice-dll
```


