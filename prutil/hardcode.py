""" hardcode constants and functions for aker project"""


from numpy import zeros, float32, uint8

#Testing:
imnet_zaglushka = ({'0': ['n00000000', 'Not implemented', 999, '100.0']}, 
                        zeros((3,1,1), dtype = float32), 
                        zeros((3,1,1), dtype = uint8), 
                        zeros((3,1,1), dtype = uint8)
                        )
# test result:
TEST_TARGETED_DICTIONARY    = {'n0': ['n0-targeted-0', 'black hole', '834', '57.02'],
                            'n1': ['n1-targered-1', 'neutron star', '906', '31.27'],
                            'n2': ['n2-targeted-3', 'blue giant', '457', '10.65']}
TEST_UNTARGETED_DICTIONARY  = {'n0': ['n0-untargeted-0', 'black hole', '834', '57.02'],
                            'n1': ['n1-untargeted-1', 'neutron star', '906', '31.27'],
                            'n2': ['n2-untargeted-3', 'blue giant', '457', '10.65']}

