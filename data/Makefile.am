SUBDIRS = layouts antler

@GSETTINGS_RULES@
@INTLTOOL_XML_NOMERGE_RULE@
gsettings_schemas_in_files = \
	org.gnome.caribou.gschema.xml.in \
	org.gnome.antler.gschema.xml.in
gsettings_SCHEMAS = $(gsettings_schemas_in_files:.gschema.xml.in=.gschema.xml)

autostartdir	 = $(sysconfdir)/xdg/autostart
autostart_in_in_files = caribou-autostart.desktop.in.in
autostart_in_files = $(autostart_in_in_files:.desktop.in.in=.desktop.in)
autostart_DATA   = $(autostart_in_files:.desktop.in=.desktop)

servicefiledir = $(datadir)/dbus-1/services
servicefile_in_files = \
	org.gnome.Caribou.Antler.service.in \
	org.gnome.Caribou.Daemon.service.in
servicefile_DATA = $(servicefile_in_files:.service.in=.service)

caribou-autostart.desktop.in: caribou-autostart.desktop.in.in
	$(AM_V_GEN)sed -e "s|[@]libexecdir[@]|$(libexecdir)|" $< > $@

org.gnome.Caribou.Antler.service: org.gnome.Caribou.Antler.service.in
	$(AM_V_GEN)sed -e "s|[@]libexecdir[@]|$(libexecdir)|" $< > $@

org.gnome.Caribou.Daemon.service: org.gnome.Caribou.Daemon.service.in
	$(AM_V_GEN)sed -e "s|[@]libexecdir[@]|$(libexecdir)|" $< > $@

@INTLTOOL_DESKTOP_RULE@

EXTRA_DIST = $(autostart_in_in_files) $(servicefile_in_files)

org.gnome.caribou.gschema.xml.in: $(top_srcdir)/caribou/settings/caribou_settings.py
	$(AM_V_GEN)$(PYTHON) -B $(top_srcdir)/tools/make_schema.py \
		-d "$(GETTEXT_PACKAGE)" \
		-o $@ caribou.settings.CaribouSettings

org.gnome.antler.gschema.xml.in: $(top_srcdir)/caribou/antler/antler_settings.py
	$(AM_V_GEN)$(PYTHON) -B $(top_srcdir)/tools/make_schema.py \
		-d "$(GETTEXT_PACKAGE)" \
		-o $@ caribou.antler.AntlerSettings

CLEANFILES = \
	$(autostart_DATA) \
	$(autostart_in_files) \
	$(gsettings_schemas_in_files) \
	$(gsettings_SCHEMAS) \
	$(servicefile_DATA)

-include $(top_srcdir)/git.mk
