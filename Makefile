PLUGINNAME = MGRS
PLUGINS = "$(HOME)"/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)
PY_FILES = __init__.py copyMgrsTool.py mgrs.py mgrsCapture.py settings.py zoomToMgrs.py
EXTRAS = metadata.txt

deploy:
	mkdir -p $(PLUGINS)
	cp -vf $(PY_FILES) $(PLUGINS)
	cp -vf $(EXTRAS) $(PLUGINS)
	cp -vfr images $(PLUGINS)
	cp -vfr ui $(PLUGINS)
	cp -vfr doc $(PLUGINS)
	cp -vf helphead.html $(PLUGINS)/index.html
	python -m markdown readme.md >> $(PLUGINS)/index.html
	echo '</body>' >> $(PLUGINS)/index.html

