import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({ selector: 'app-root', standalone: true, template: `<main><h1>DT Dashboard</h1><p>Angular 20 frontend foundation</p></main>`, styles: [`main{font-family:system-ui,sans-serif;padding:2rem}`], changeDetection: ChangeDetectionStrategy.OnPush })
export class AppComponent {}
