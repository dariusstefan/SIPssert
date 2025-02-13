#!/usr/bin/env python
##
## This file is part of the SIPssert Testing Framework project
## Copyright (C) 2023 OpenSIPS Solutions
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##


"""Implementation of the brided network type"""

import docker
from sipssert.network import network
from sipssert import logger

class OverlayNetworkBadConfig(network.NetworkBadConfig): # pylint: disable=too-few-public-methods
    """Invalid config for Overlay Network"""

class OverlayNetworkOperation(network.NetworkError): # pylint: disable=too-few-public-methods
    """Operations error for Overlay Network"""

class OverlayNetwork(network.Network):
    """Overlay Network adapter"""

    net_type = "Overlay"

    """Implemention about of the 'Overlay' network type"""

    def __init__(self, controller, network_config):

        try:
            self.controller = controller
            self.name = network_config["name"]
            self.subnet = network_config["subnet"]
            self.gateway = network_config["gateway"]
            self.created = False
        except KeyError as exc:
            raise OverlayNetworkBadConfig("invalid setting") from exc

        self.setup()

    def setup(self):
        """Sets up the network"""
        try:
            ipam_pool = docker.types.IPAMPool(subnet=self.subnet,
                                              gateway=self.gateway)
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

            self.controller.docker.networks.create(self.name,
                                                   driver="overlay",
                                                   ipam=ipam_config,
                                                   attachable=True,
                                                   scope="global")
            self.created = True
        except docker.errors.APIError as err:
            emsg = f"cannot create Overlay adapter {self.name}"
            logger.slog.error(emsg)
            logger.slog.exception(err)
            raise OverlayNetworkOperation(emsg) from err
        logger.slog.info("Overlay adapter %s successfully created!", self.name)


    def destroy(self):
        """Destroys the network"""
        if not self.created:
            return
        if self.controller.no_delete:
            return
        try:
            self.controller.docker.networks.get(self.name).remove()
            self.created = False
            logger.slog.debug("Overlay adapter %s destroyed!", self.name)
        except docker.errors.NotFound:
            logger.slog.debug("Overlay adapter %s not found!", self.name)
            self.created = False
        except docker.errors.APIError:
            logger.slog.exception("could not remove adapter %s!", self.name)

    def __del__(self):
        """Deletes the network in case destroy is missed"""
        self.destroy()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
