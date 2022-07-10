import json
import time

import socketio

from . import AuthMethod
from . import MonitorType
from . import NotificationType, notification_provider_options
from . import ProxyProtocol
from . import IncidentStyle
from . import convert_from_socket, convert_to_socket, params_map_monitor, params_map_notification, \
    params_map_notification_provider, params_map_proxy, params_map_status_page, params_map_info, \
    params_map_settings
from . import UptimeKumaException

params_map_notification_and_provider = {**params_map_notification, **params_map_notification_provider}


def int_to_bool(data, keys):
    if type(data) == list:
        for d in data:
            int_to_bool(d, keys)
    else:
        for key in keys:
            if key in data:
                data[key] = True if data[key] == 1 else False


def _build_monitor_data(
        type_: MonitorType,
        name: str,
        heartbeat_interval: int = 60,
        heartbeat_retry_interval: int = 60,
        retries: int = 0,
        upside_down_mode: bool = False,
        tags: list = None,
        notification_ids: list[int] = None,

        # HTTP, KEYWORD
        url: str = None,
        certificate_expiry_notification: bool = False,
        ignore_tls_error: bool = False,
        max_redirects: int = 10,
        accepted_status_codes: list[str] = None,
        proxy_id: int = None,
        http_method: str = "GET",
        http_body: str = None,
        http_headers: str = None,
        auth_method: AuthMethod = AuthMethod.NONE,
        auth_user: str = None,
        auth_pass: str = None,
        auth_domain: str = None,
        auth_workstation: str = None,

        # KEYWORD
        keyword: str = None,

        # DNS, PING, STEAM, MQTT
        hostname: str = None,

        # DNS, STEAM, MQTT
        port: int = 53,

        # DNS
        dns_resolve_server: str = "1.1.1.1",
        dns_resolve_type: str = "A",

        # MQTT
        mqtt_username: str = None,
        mqtt_password: str = None,
        mqtt_topic: str = None,
        mqtt_success_message: str = None,

        # SQLSERVER
        sqlserver_connection_string: str = "Server=<hostname>,<port>;Database=<your database>;User Id=<your user id>;Password=<your password>;Encrypt=<true/false>;TrustServerCertificate=<Yes/No>;Connection Timeout=<int>",
        sqlserver_query: str = None,
):
    if not accepted_status_codes:
        accepted_status_codes = ["200-299"]

    dict_notification_ids = {}
    if notification_ids:
        for notification_id in notification_ids:
            dict_notification_ids[notification_id] = True
    notification_ids = dict_notification_ids

    data = {
        "type_": type_,
        "name": name,
        "heartbeat_interval": heartbeat_interval,
        "heartbeat_retry_interval": heartbeat_retry_interval,
        "retries": retries,
        "notification_ids": notification_ids,
        "upside_down_mode": upside_down_mode,
    }

    if tags:
        data.update({
            "tags": tags
        })

    if type_ == MonitorType.KEYWORD:
        data.update({
            "keyword": keyword,
        })

    # HTTP, KEYWORD
    data.update({
        "url": url,
        "certificate_expiry_notification": certificate_expiry_notification,
        "ignore_tls_error": ignore_tls_error,
        "max_redirects": max_redirects,
        "accepted_status_codes": accepted_status_codes,
        "proxy_id": proxy_id,
        "http_method": http_method,
        "http_body": http_body,
        "http_headers": http_headers,
        "auth_method": auth_method,
    })

    if auth_method in [AuthMethod.HTTP_BASIC, AuthMethod.NTLM]:
        data.update({
            "auth_user": auth_user,
            "auth_pass": auth_pass,
        })

    if auth_method == AuthMethod.NTLM:
        data.update({
            "auth_domain": auth_domain,
            "auth_workstation": auth_workstation,
        })

    # DNS, PING, STEAM, MQTT
    data.update({
        "hostname": hostname,
    })

    # DNS, STEAM, MQTT
    data.update({
        "port": port,
    })

    # DNS
    data.update({
        "dns_resolve_server": dns_resolve_server,
        "dns_resolve_type": dns_resolve_type,
    })

    # MQTT
    data.update({
        "mqtt_username": mqtt_username,
        "mqtt_password": mqtt_password,
        "mqtt_topic": mqtt_topic,
        "mqtt_success_message": mqtt_success_message,
    })

    # SQLSERVER
    data.update({
        "sqlserver_connection_string": sqlserver_connection_string
    })
    if type_ == MonitorType.SQLSERVER:
        data.update({
            "sqlserver_query": sqlserver_query,
        })

    data = convert_to_socket(params_map_monitor, data)
    return data


def _build_notification_data(name: str, type_: NotificationType, default: bool = False, apply_existing: bool = False, **kwargs):
    data = {
        "name": name,
        "type_": type_,
        "default": default,
        **kwargs
    }
    data = convert_to_socket(params_map_notification_and_provider, data)
    return data


def _build_proxy_data(
        protocol: ProxyProtocol,
        host: str,
        port: str,
        auth: bool = False,
        username: str = None,
        password: str = None,
        active: bool = True,
        default: bool = False,
        apply_existing: bool = False,
):
    data = {
        "protocol": protocol,
        "host": host,
        "port": port,
        "auth": auth,
        "username": username,
        "password": password,
        "active": active,
        "default": default,
        "apply_existing": apply_existing
    }
    data = convert_to_socket(params_map_proxy, data)
    return data


def _build_status_page_data(
        slug: str,

        # config
        id_: int,
        title: str,
        description: str = None,
        theme: str = "light",
        published: bool = True,
        show_tags: bool = False,
        domain_name_list: list[str] = None,
        custom_css: str = "",
        footer_text: str = None,
        show_powered_by: bool = True,

        img_data_url: str = "/icon.svg",
        monitors: list = None
):
    if theme not in ["light", "dark"]:
        raise ValueError
    if not domain_name_list:
        domain_name_list = []
    public_group_list = []
    if monitors:
        public_group_list.append({
            "name": "Services",
            "monitorList": monitors
        })
    config = {
        "id_": id_,
        "slug": slug,
        "title": title,
        "description": description,
        "img_data_url": img_data_url,
        "theme": theme,
        "published": published,
        "show_tags": show_tags,
        "domain_name_list": domain_name_list,
        "custom_css": custom_css,
        "footer_text": footer_text,
        "show_powered_by": show_powered_by
    }
    config = convert_to_socket(params_map_status_page, config)
    return slug, config, img_data_url, public_group_list


def _check_missing_arguments(required_params, kwargs, params_map):
    missing_arguments = []
    for required_param in required_params:
        required_param_sock = convert_to_socket(params_map, required_param)
        if kwargs.get(required_param_sock) is None:
            missing_arguments.append(required_param)
    if missing_arguments:
        missing_arguments_str = ", ".join([f"'{i}'" for i in missing_arguments])
        raise TypeError(f"missing {len(missing_arguments)} required argument: {missing_arguments_str}")


def _check_argument_conditions(valid_params, kwargs, params_map):
    for valid_param in valid_params:
        valid_param_sock = convert_to_socket(params_map, valid_param)
        if valid_param_sock in kwargs:
            value = kwargs[valid_param_sock]
            conditions = valid_params[valid_param]
            min_ = conditions.get("min")
            max_ = conditions.get("max")
            if min_ is not None and value < min_:
                raise ValueError(f"the value of {valid_param} must not be less than {min_}")
            if max_ is not None and value > max_:
                raise ValueError(f"the value of {valid_param} must not be larger than {max_}")


def _check_arguments_monitor(kwargs):
    required_args = [
        "type_",
        "name",
        "heartbeat_interval",
        "retries",
        "heartbeat_retry_interval"
    ]
    _check_missing_arguments(required_args, kwargs, params_map_monitor)

    required_args_by_type = {
        MonitorType.HTTP: ["url", "max_redirects"],
        MonitorType.PORT: ["hostname", "port"],
        MonitorType.PING: ["hostname"],
        MonitorType.KEYWORD: ["url", "keyword", "max_redirects"],
        MonitorType.DNS: ["hostname", "dns_resolve_server", "port"],
        MonitorType.PUSH: [],
        MonitorType.STEAM: ["hostname", "port"],
        MonitorType.MQTT: ["hostname", "port", "mqtt_topic"],
        MonitorType.SQLSERVER: [],
    }
    type_ = kwargs[convert_to_socket(params_map_monitor, "type")]
    required_args = required_args_by_type[type_]
    _check_missing_arguments(required_args, kwargs, params_map_monitor)

    conditions = {
        "heartbeat_interval": {
            "min": 20
        },
        "retries": {
            "min": 0
        },
        "heartbeat_retry_interval": {
            "min": 20
        },
        "max_redirects": {
            "min": 0
        },
        "port": {
            "min": 0,
            "max": 65535
        }
    }
    _check_argument_conditions(conditions, kwargs, params_map_monitor)


def _check_arguments_notification(kwargs):
    required_args = ["type_", "name"]
    _check_missing_arguments(required_args, kwargs, params_map_notification_and_provider)

    type_ = kwargs[convert_to_socket(params_map_notification, "type")]
    required_args_sock = notification_provider_options[type_]
    required_args = convert_from_socket(params_map_notification_provider, required_args_sock)
    _check_missing_arguments(required_args, kwargs, params_map_notification_and_provider)

    provider_conditions = {
        'gotify_priority': {
            'max': 10,
            'min': 0
        },
        'ntfy_priority': {
            'max': 5,
            'min': 1
        },
        'smtp_smtp_port': {
            'max': 65535,
            'min': 0
        }
    }
    _check_argument_conditions(provider_conditions, kwargs, params_map_notification_and_provider)


def _check_arguments_proxy(kwargs):
    required_args = ["protocol", "host", "port"]
    if "auth" in kwargs:
        required_args.extend(["username", "password"])
    _check_missing_arguments(required_args, kwargs, params_map_proxy)

    conditions = {
        "port": {
            "min": 0,
            "max": 65535
        }
    }
    _check_argument_conditions(conditions, kwargs, params_map_proxy)


class UptimeKumaApi(object):
    def __init__(self, url):
        self.sio = socketio.Client()

        self._event_data: dict[str, any] = {
            "monitorList": None,
            "notificationList": None,
            "proxyList": None,
            "statusPageList": None,
            "heartbeatList": None,
            "importantHeartbeatList": None,
            "avgPing": None,
            "uptime": None,
            "heartbeat": None,
            "info": None,
        }

        self.sio.on("connect", self._event_connect)
        self.sio.on("disconnect", self._event_disconnect)
        self.sio.on("monitorList", self._event_monitor_list)
        self.sio.on("notificationList", self._event_notification_list)
        self.sio.on("proxyList", self._event_proxy_list)
        self.sio.on("statusPageList", self._event_status_page_list)
        self.sio.on("heartbeatList", self._event_heartbeat_list)
        self.sio.on("importantHeartbeatList", self._event_important_heartbeat_list)
        self.sio.on("avgPing", self._event_avg_ping)
        self.sio.on("uptime", self._event_uptime)
        self.sio.on("heartbeat", self._event_heartbeat)
        self.sio.on("info", self._event_info)

        self.connect(url)

    def _get_event_data(self, event):
        while self._event_data[event] is None:
            time.sleep(0.01)
        time.sleep(0.01)  # wait for multiple messages
        return self._event_data[event]

    def _call(self, event, data=None):
        r = self.sio.call(event, data)
        if type(r) == dict and "ok" in r:
            if not r["ok"]:
                raise UptimeKumaException(r["msg"])
            r.pop("ok")
        return r

    # event handlers

    def _event_connect(self):
        pass

    def _event_disconnect(self):
        pass

    def _event_monitor_list(self, data):
        self._event_data["monitorList"] = data

    def _event_notification_list(self, data):
        self._event_data["notificationList"] = data

    def _event_proxy_list(self, data):
        self._event_data["proxyList"] = data

    def _event_status_page_list(self, data):
        self._event_data["statusPageList"] = data

    def _event_heartbeat_list(self, id_, data, bool_):
        if self._event_data["heartbeatList"] is None:
            self._event_data["heartbeatList"] = []
        self._event_data["heartbeatList"].append({
            "id": id_,
            "data": data,
            "bool": bool_,
        })

    def _event_important_heartbeat_list(self, id_, data, bool_):
        if self._event_data["importantHeartbeatList"] is None:
            self._event_data["importantHeartbeatList"] = []
        self._event_data["importantHeartbeatList"].append({
            "id": id_,
            "data": data,
            "bool": bool_,
        })

    def _event_avg_ping(self, id_, data):
        if self._event_data["avgPing"] is None:
            self._event_data["avgPing"] = []
        self._event_data["avgPing"].append({
            "id": id_,
            "data": data,
        })

    def _event_uptime(self, id_, hours_24, days_30):
        if self._event_data["uptime"] is None:
            self._event_data["uptime"] = []
        self._event_data["uptime"].append({
            "id": id_,
            "hours_24": hours_24,
            "days_30": days_30,
        })

    def _event_heartbeat(self, data):
        if self._event_data["heartbeat"] is None:
            self._event_data["heartbeat"] = []
        self._event_data["heartbeat"].append(data)

    def _event_info(self, data):
        self._event_data["info"] = data

    # connection

    def connect(self, url: str):
        url = url.rstrip("/")
        self.sio.connect(f'{url}/socket.io/')

    def disconnect(self):
        self.sio.disconnect()

    # monitors

    def get_monitors(self):
        r = list(self._get_event_data("monitorList").values())
        r = convert_from_socket(params_map_monitor, r)
        int_to_bool(r, ["active"])
        return r

    def get_monitor(self, id_: int):
        r = self._call('getMonitor', id_)["monitor"]
        r = convert_from_socket(params_map_monitor, r)
        int_to_bool(r, ["active"])
        return r

    def pause_monitor(self, id_: int):
        return self._call('pauseMonitor', id_)

    def resume_monitor(self, id_: int):
        return self._call('resumeMonitor', id_)

    def delete_monitor(self, id_: int):
        return self._call('deleteMonitor', id_)

    def get_monitor_beats(self, id_: int, hours: int):
        r = self._call('getMonitorBeats', (id_, hours))["data"]
        int_to_bool(r, ["important", "status"])
        return r

    def add_monitor(self, **kwargs):
        data = _build_monitor_data(**kwargs)

        _check_arguments_monitor(data)
        r = self._call('add', data)

        r = convert_from_socket(params_map_monitor, r)
        return r

    def edit_monitor(self, id_: int, **kwargs):
        data = self.get_monitor(id_)
        data.update(kwargs)
        data = convert_to_socket(params_map_monitor, data)

        _check_arguments_monitor(data)
        r = self._call('editMonitor', data)

        r = convert_from_socket(params_map_monitor, r)
        return r

    # monitor tags

    def add_monitor_tag(self, tag_id: int, monitor_id: int, value=""):
        return self._call('addMonitorTag', (tag_id, monitor_id, value))

    # editMonitorTag is unused in uptime-kuma
    # def edit_monitor_tag(self, tag_id: int, monitor_id: int, value=""):
    #     return self._call('editMonitorTag', (tag_id, monitor_id, value))

    def delete_monitor_tag(self, tag_id: int, monitor_id: int, value=""):
        return self._call('deleteMonitorTag', (tag_id, monitor_id, value))

    # notifications

    def get_notifications(self):
        notifications = self._get_event_data("notificationList")
        r = []
        for notification_raw in notifications:
            notification = notification_raw.copy()
            config = json.loads(notification["config"])
            del notification["config"]
            notification.update(config)
            r.append(notification)
        r = convert_from_socket(params_map_notification_and_provider, r)
        return r

    def get_notification(self, id_: int):
        notifications = self.get_notifications()
        for notification in notifications:
            if notification["id"] == id_:
                return notification
        raise UptimeKumaException("notification does not exist")

    def test_notification(self, **kwargs):
        data = _build_notification_data(**kwargs)

        _check_arguments_notification(data)
        return self._call('testNotification', data)

    def add_notification(self, **kwargs):
        data = _build_notification_data(**kwargs)

        _check_arguments_notification(data)
        return self._call('addNotification', (data, None))

    def edit_notification(self, id_: int, **kwargs):
        notification = self.get_notification(id_)

        # remove old notification provider options from notification object
        if "type_" in kwargs and kwargs != notification["type_"]:
            for provider in notification_provider_options:
                provider_options = notification_provider_options[provider]
                if provider != kwargs:
                    for option in provider_options:
                        if option in notification:
                            del notification[option]

        notification.update(kwargs)
        notification = convert_to_socket(params_map_notification_and_provider, notification)

        _check_arguments_notification(notification)
        return self._call('addNotification', (notification, id_))

    def delete_notification(self, id_: int):
        return self._call('deleteNotification', id_)

    def check_apprise(self):
        return self._call('checkApprise')

    # proxy

    def get_proxies(self):
        r = self._get_event_data("proxyList")
        r = convert_from_socket(params_map_proxy, r)
        int_to_bool(r, ["auth", "active", "default", "apply_existing"])
        return r

    def get_proxy(self, id_: int):
        proxies = self.get_proxies()
        for proxy in proxies:
            if proxy["id"] == id_:
                return proxy
        raise UptimeKumaException("proxy does not exist")

    def add_proxy(self, **kwargs):
        data = _build_proxy_data(**kwargs)

        _check_arguments_proxy(data)
        return self._call('addProxy', (data, None))

    def edit_proxy(self, id_: int, **kwargs):
        proxy = self.get_proxy(id_)
        proxy.update(kwargs)
        proxy = convert_to_socket(params_map_proxy, proxy)

        _check_arguments_proxy(proxy)
        return self._call('addProxy', (proxy, id_))

    def delete_proxy(self, id_: int):
        return self._call('deleteProxy', id_)

    # status page

    def get_status_pages(self):
        r = list(self._get_event_data("statusPageList").values())
        r = convert_from_socket(params_map_status_page, r)
        return r

    def get_status_page(self, slug: str):
        r = self._call('getStatusPage', slug)
        config = r["config"]
        del r["config"]
        r.update(config)
        r = convert_from_socket(params_map_status_page, r)
        return r

    def add_status_page(self, slug: str, title: str):
        return self._call('addStatusPage', (title, slug))

    def delete_status_page(self, slug: str):
        return self._call('deleteStatusPage', slug)

    def save_status_page(self, slug: str, **kwargs):
        status_page = self.get_status_page(slug)
        status_page.update(kwargs)
        data = _build_status_page_data(**status_page)
        return self._call('saveStatusPage', data)

    def post_incident(
            self,
            slug: str,
            title: str,
            content: str,
            style: IncidentStyle = IncidentStyle.PRIMARY
    ):
        incident = {
            "title": title,
            "content": content,
            "style": style
        }
        r = self._call('postIncident', (slug, incident))["incident"]
        r = convert_from_socket(params_map_status_page, r)
        self.save_status_page(slug)
        return r

    def unpin_incident(self, slug: str):
        r = self._call('unpinIncident', slug)
        self.save_status_page(slug)
        return r

    # heartbeat

    def get_heartbeats(self):
        r = self._get_event_data("heartbeatList")
        for i in r:
            int_to_bool(i["data"], ["important", "status"])
        return r

    def get_important_heartbeats(self):
        r = self._get_event_data("importantHeartbeatList")
        for i in r:
            int_to_bool(i["data"], ["important", "status"])
        return r

    def get_heartbeat(self):
        r = self._get_event_data("heartbeat")
        int_to_bool(r, ["important", "status"])
        return r

    # avg ping

    def avg_ping(self):
        return self._get_event_data("avgPing")

    # uptime

    def uptime(self):
        return self._get_event_data("uptime")

    # info

    def info(self):
        r = self._get_event_data("info")
        r = convert_from_socket(params_map_info, r)
        return r

    # clear

    def clear_events(self, monitor_id: int):
        return self._call('clearEvents', monitor_id)

    def clear_heartbeats(self, monitor_id: int):
        return self._call('clearHeartbeats', monitor_id)

    def clear_statistics(self):
        return self._call('clearStatistics')

    # tags

    def get_tags(self):
        return self._call('getTags')["tags"]

    def get_tag(self, id_: int):
        tags = self.get_tags()
        for tag in tags:
            if tag["id"] == id_:
                return tag
        raise UptimeKumaException("tag does not exist")

    # not working, monitor id required?
    # def edit_tag(self, id_: int, name: str, color: str):
    #     return self._call('editTag', {
    #         "id": id_,
    #         "name": name,
    #         "color": color
    #     })

    def delete_tag(self, id_: int):
        return self._call('deleteTag', id_)

    def add_tag(self, name: str, color: str):
        return self._call('addTag', {
            "name": name,
            "color": color,
            "new": True
        })["tag"]

    # settings

    def get_settings(self):
        r = self._call('getSettings')["data"]
        r = convert_from_socket(params_map_settings, r)
        return r

    def set_settings(
            self,
            password: str,

            # about
            check_update: bool = True,
            check_beta: bool = False,

            # monitor history
            keep_data_period_days: int = 180,

            # general
            entry_page: str = "dashboard",
            search_engine_index: bool = False,
            primary_base_url: str = "",
            steam_api_key: str = "",

            # notifications
            tls_expiry_notify_days: list[int] = None,

            # security
            disable_auth: bool = False
    ):
        if not tls_expiry_notify_days:
            tls_expiry_notify_days = [7, 14, 21]

        data = {
            "check_update": check_update,
            "check_beta": check_beta,
            "keep_data_period_days": keep_data_period_days,
            "entry_page": entry_page,
            "search_engine_index": search_engine_index,
            "primary_base_url": primary_base_url,
            "steam_api_key": steam_api_key,
            "tls_expiry_notify_days": tls_expiry_notify_days,
            "disable_auth": disable_auth
        }
        data = convert_to_socket(params_map_settings, data)
        return self._call('setSettings', (data, password))

    def change_password(self, old_password: str, new_password: str):
        return self._call('changePassword', {
            "currentPassword": old_password,
            "newPassword": new_password,
        })

    def upload_backup(self, json_data, import_handle: str):
        if import_handle not in ["overwrite", "skip", "keep"]:
            raise ValueError()
        return self._call('uploadBackup', (json_data, import_handle))

    # 2FA

    def twofa_status(self):
        return self._call('twoFAStatus')

    def prepare_2fa(self, password: str):
        return self._call('prepare2FA', password)

    def save_2fa(self, password: str):
        return self._call('save2FA', password)

    def disable_2fa(self, password: str):
        return self._call('disable2FA', password)

    # login

    def login(self, username: str, password: str):
        return self._call('login', {
            "username": username,
            "password": password,
            "token": ""
        })

    def login_by_token(self, token: str):
        return self._call('loginByToken', token)

    def verify_token(self, token: str, password: str):
        return self._call('verifyToken', (token, password))

    def logout(self):
        return self._call('logout')

    # setup

    def need_setup(self):
        return self._call('needSetup')

    def setup(self, username: str, password: str):
        return self._call("setup", (username, password))

    # database

    def get_database_size(self):
        return self._call('getDatabaseSize')

    def shrink_database(self):
        return self._call('shrinkDatabase')
